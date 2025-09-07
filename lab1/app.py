import tkinter as tk
from tkinter import ttk, messagebox, filedialog


import threading
import queue
import platform
import numpy as np
import sounddevice as sd
import soundfile as sf

from vu_led_canvas import VuLedCanvas
from wave_canvas import WaveCanvas
from async_level_meter import AsyncLevelMeter
from output_player import OutputPlayer


FS_OPTIONS = [8000, 16000, 22050, 44100, 48000]

def moving_average(x: np.ndarray, M: int) -> np.ndarray:
    M = max(1, int(M))
    kernel = np.ones(M, dtype=np.float64) / M
    y = np.convolve(x.astype(np.float64), kernel, mode="same")
    return y.astype(np.float32)

# ------------- Main App -------------
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Laboratorio 1 - Player visual (nivel + forma de onda)")
        self.root.geometry("880x620")
        self.root.minsize(860, 600)

        # Estado
        self.signal = None            # (x, fs)
        self.signal_filtered = None   # (y, fs)

        self.fs = tk.IntVar(value=44100)
        self.dur = tk.DoubleVar(value=3.0)
        self.M = tk.IntVar(value=5)
        self.raw_capture = tk.BooleanVar(value=False)

        self.devices, self.hostapis = self._enumerate_devices()
        self.device_labels = [f"{i}: {d['name']}  [{self.hostapis.get(d['hostapi'], '?')}]" for i, d in enumerate(self.devices) if d.get('max_input_channels',0)>0]
        default_label = self.device_labels[0] if self.device_labels else "No hay dispositivos de entrada"
        self.selected_device = tk.StringVar(value=default_label)

        # Components
        self.input_meter = AsyncLevelMeter()
        self.output_player = OutputPlayer()

        self._build_ui()
        self._restart_input_meter()

        # observers
        self.fs.trace_add("write", lambda *args: self._restart_input_meter())
        self.selected_device.trace_add("write", lambda *args: self._restart_input_meter())
        self.raw_capture.trace_add("write", lambda *args: self._restart_input_meter())

        # timers
        self._tick_input_ui()
        self._tick_output_ui()

    def _build_ui(self):
        accent = "#2563eb"
        bg_card = "#f8fafc"
        self.root.configure(bg="white")
        style = ttk.Style(self.root)
        try:
            self.root.call("ttk::style", "theme", "use", "clam")
        except tk.TclError:
            pass
        style.configure("TButton", padding=6)
        style.configure("TLabelframe", background="white")
        style.configure("TLabelframe.Label", background="white")
        style.configure("TFrame", background="white")
        style.configure("TLabel", background="white")
        style.configure("TCheckbutton", background="white")

        main = ttk.Frame(self.root, padding=12)
        main.pack(fill=tk.BOTH, expand=True)

        # --- Adquisición ---
        params = ttk.LabelFrame(main, text="Adquisición", padding=10)
        params.pack(fill=tk.X, pady=(0,10))

        ttk.Label(params, text="Micrófono").grid(row=0, column=0, padx=6, pady=(8,2), sticky="w")
        self.device_cb = ttk.Combobox(params, values=self.device_labels, textvariable=self.selected_device, state="readonly", width=60)
        self.device_cb.grid(row=0, column=1, columnspan=3, padx=6, pady=(8,2), sticky="w")

        ttk.Label(params, text="Nivel de entrada").grid(row=1, column=0, padx=6, pady=(0,8), sticky="w")
        self.in_vu = VuLedCanvas(params, bars=24, bg=bg_card, highlightthickness=0, bd=0)
        self.in_vu.grid(row=1, column=1, columnspan=2, padx=6, pady=(0,8), sticky="we")
        self.in_db = ttk.Label(params, text="-∞ dBFS")
        self.in_db.grid(row=1, column=3, padx=6, pady=(0,8), sticky="e")

        ttk.Label(params, text="Frecuencia (Hz)").grid(row=2, column=0, padx=6, pady=6, sticky="w")
        ttk.Combobox(params, values=FS_OPTIONS, textvariable=self.fs, state="readonly", width=12).grid(row=2, column=1, padx=6, pady=6)

        ttk.Label(params, text="Ventana M (filtro)").grid(row=2, column=2, padx=6, pady=6, sticky="e")
        ttk.Spinbox(params, from_=2, to=128, textvariable=self.M, width=8).grid(row=2, column=3, padx=6, pady=6)

        ttk.Label(params, text="Duración (s)").grid(row=3, column=0, padx=6, pady=6, sticky="w")
        ttk.Entry(params, textvariable=self.dur, width=12).grid(row=3, column=1, padx=6, pady=6)

        self.raw_chk = ttk.Checkbutton(params, text="Intentar captura sin procesamiento (RAW / exclusivo)", variable=self.raw_capture)
        self.raw_chk.grid(row=3, column=2, columnspan=2, padx=6, pady=6, sticky="w")

        # --- Acciones captura/filtro ---
        actions = ttk.LabelFrame(main, text="Acciones de señal", padding=10)
        actions.pack(fill=tk.X, pady=(0,10))
        ttk.Button(actions, text="● Grabar", command=self.on_record).grid(row=0, column=0, padx=6, pady=6)
        ttk.Button(actions, text="Aplicar filtro (M)", command=self.on_apply_filter).grid(row=0, column=1, padx=6, pady=6)
        ttk.Button(actions, text="💾 Guardar WAVs", command=self.on_save).grid(row=0, column=2, padx=6, pady=6)

        # --- Player ---
        player = ttk.LabelFrame(main, text="Reproductor visual", padding=10)
        player.pack(fill=tk.BOTH, expand=True)

        ttk.Label(player, text="Pista").grid(row=0, column=0, padx=6, pady=6, sticky="e")
        self.track_var = tk.StringVar(value="Original")
        ttk.Combobox(player, values=["Original", "Filtrado"], textvariable=self.track_var, state="readonly", width=12).grid(row=0, column=1, padx=6, pady=6, sticky="w")

        ttk.Button(player, text="▶ Play", command=self.on_play).grid(row=0, column=2, padx=6, pady=6)
        ttk.Button(player, text="⏸ Pausa", command=self.on_pause).grid(row=0, column=3, padx=6, pady=6)
        ttk.Button(player, text="■ Stop", command=self.on_stop).grid(row=0, column=4, padx=6, pady=6)

        ttk.Label(player, text="Progreso").grid(row=1, column=0, padx=6, pady=6, sticky="e")
        self.progress = tk.DoubleVar(value=0.0)
        self.progress_scale = ttk.Scale(player, from_=0.0, to=1.0, variable=self.progress, command=self.on_seek)
        self.progress_scale.grid(row=1, column=1, columnspan=4, padx=6, pady=6, sticky="we")

        # Output VU + dB
        ttk.Label(player, text="Nivel de salida").grid(row=2, column=0, padx=6, pady=(6,2), sticky="e")
        self.out_vu = VuLedCanvas(player, bars=24, bg=bg_card, highlightthickness=0, bd=0)
        self.out_vu.grid(row=2, column=1, columnspan=3, padx=6, pady=(6,2), sticky="we")
        self.out_db = ttk.Label(player, text="-∞ dBFS")
        self.out_db.grid(row=2, column=4, padx=6, pady=(6,2), sticky="w")

        # Waveform scope
        ttk.Label(player, text="Forma de onda (ventana reciente)").grid(row=3, column=0, padx=6, pady=(6,2), sticky="e")
        self.scope = WaveCanvas(player)
        self.scope.grid(row=3, column=1, columnspan=4, padx=6, pady=(6,12), sticky="we")

        # grid weights
        player.grid_columnconfigure(1, weight=1)
        player.grid_columnconfigure(2, weight=0)
        player.grid_columnconfigure(3, weight=0)
        player.grid_columnconfigure(4, weight=0)

        info = ttk.Frame(main)
        info.pack(fill=tk.X, pady=(6,0))
        self.status_var = tk.StringVar(value="Graba, aplica filtro si quieres, luego usa el reproductor visual.")
        ttk.Label(info, textvariable=self.status_var, foreground="#374151").pack(side=tk.LEFT)

    # ---------- Enumeración de dispositivos ----------
    def _enumerate_devices(self):
        try:
            devices = sd.query_devices()
            hostapis_info = sd.query_hostapis()
            hostapis = {i: h['name'] for i, h in enumerate(hostapis_info)}
            return devices, hostapis
        except Exception:
            return [], {}

    def _parse_dev_index(self, label: str):
        try:
            return int(label.split(":")[0]) if ":" in label else None
        except Exception:
            return None

    # ---------- Input meter control ----------
    def _restart_input_meter(self):
        dev_idx = self._parse_dev_index(self.selected_device.get())
        fs = int(self.fs.get())
        raw = bool(self.raw_capture.get())
        self.input_meter.start(dev_idx, fs, raw)

    def _tick_input_ui(self):
        latest = None
        try:
            while True:
                latest = self.input_meter.q.get_nowait()
        except queue.Empty:
            pass
        if latest is not None:
            eps = 1e-9
            db = 20.0 * float(np.log10(max(eps, latest)))
            norm = float(np.clip(latest * 3.0, 0.0, 1.0))
            self.in_vu.update_level(norm)
            self.in_db.config(text=f"{db:5.1f} dBFS")
        self.root.after(40, self._tick_input_ui)

    # ---------- Output UI tick ----------
    def _tick_output_ui(self):
        # nivel
        lev = None
        try:
            while True:
                lev = self.output_player.level_q.get_nowait()
        except queue.Empty:
            pass
        if lev is not None:
            eps = 1e-9
            db = 20.0 * float(np.log10(max(eps, lev)))
            norm = float(np.clip(lev * 3.0, 0.0, 1.0))
            self.out_vu.update_level(norm)
            self.out_db.config(text=f"{db:5.1f} dBFS")

        # scope
        scope = None
        try:
            while True:
                scope = self.output_player.scope_q.get_nowait()
        except queue.Empty:
            pass
        if scope is not None:
            self.scope.draw_wave(scope)

        # progreso
        self.progress.set(self.output_player.progress())

        self.root.after(33, self._tick_output_ui)  # ~30 FPS

    # ---------- Señal: grabar / filtrar / guardar ----------
    def on_record(self):
        try:
            fs = int(self.fs.get())
            dur = float(self.dur.get())
            if fs <= 0 or dur <= 0:
                raise ValueError("Parámetros inválidos: verifique Fs y duración.")
        except Exception as e:
            messagebox.showerror("Error de parámetros", str(e))
            return
        threading.Thread(target=self._record_worker, args=(fs, dur), daemon=True).start()

    def _record_worker(self, fs, dur):
        try:
            self.status_var.set("Grabando...")
            dev_idx = self._parse_dev_index(self.selected_device.get())
            extra = None
            if self.raw_capture.get() and platform.system() == "Windows":
                try:
                    extra = sd.WasapiSettings(exclusive=True)
                except Exception:
                    extra = None
            x = sd.rec(int(dur * fs), samplerate=fs, channels=1, dtype="float32", device=dev_idx,
                       latency="low", extra_settings=extra)
            sd.wait()
            x = x.flatten()
            self.signal = (x, fs)
            self.signal_filtered = None
            self.status_var.set(f"Grabación lista: {len(x)} muestras @ {fs} Hz.")
        except Exception as e:
            self.status_var.set("Error.")
            messagebox.showerror("Error al grabar", str(e))

    def on_apply_filter(self):
        if not self.signal:
            messagebox.showwarning("Atención", "Primero graba una señal.")
            return
        x, fs = self.signal
        try:
            M = int(self.M.get())
            y = moving_average(x, M)
            self.signal_filtered = (y, fs)
            self.status_var.set(f"Filtro aplicado (M={M}). Ya puedes reproducir el audio filtrado.")
        except Exception as e:
            messagebox.showerror("Error al filtrar", str(e))

    def on_save(self):
        if not self.signal:
            messagebox.showwarning("Atención", "Nada que guardar: no hay señal original.")
            return
        x, fs = self.signal
        base = filedialog.asksaveasfilename(
            title="Guardar como... (se generarán sufijos)",
            defaultextension=".wav",
            filetypes=[("WAV","*.wav")]
        )
        if not base:
            return
        stem = base[:-4] if base.lower().endswith(".wav") else base
        try:
            sf.write(stem + "_original.wav", x, fs, subtype="PCM_16")
            if self.signal_filtered:
                y, fs2 = self.signal_filtered
                sf.write(stem + f"_filtrado_M{self.M.get()}.wav", y, fs2, subtype="PCM_16")
            messagebox.showinfo("Guardado", "Archivos WAV guardados correctamente.")
        except Exception as e:
            messagebox.showerror("Error al guardar", str(e))

    # ---------- Player controls ----------
    def _resolve_track(self):
        if self.track_var.get() == "Filtrado":
            if self.signal_filtered:
                return self.signal_filtered
            else:
                messagebox.showwarning("Atención", "No hay pista filtrada. Aplica el filtro primero.")
                return None
        else:
            if self.signal:
                return self.signal
            else:
                messagebox.showwarning("Atención", "No hay pista original.")
                return None

    def on_play(self):
        track = self._resolve_track()
        if not track:
            return
        x, fs = track
        self.output_player.load(x, fs)
        self.output_player.play()
        self.status_var.set(f"Reproduciendo {self.track_var.get()}...")

    def on_pause(self):
        self.output_player.pause()
        self.status_var.set("Pausado.")

    def on_stop(self):
        self.output_player.stop()
        self.status_var.set("Detenido.")

    def on_seek(self, _val):
        self.output_player.seek_frac(float(self.progress.get()))
