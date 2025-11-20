import os
import numpy as np
import matplotlib.pyplot as plt

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import filedialog, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from dct_manual import transformada_dct, transformada_idct
from procesar_imagen import (
    aplicar_dct_por_bloques,
    aplicar_idct_por_bloques,
    _leer_imagen_grises,
)

IMG_FILETYPES = [
    ("Imagenes", "*.png *.jpg *.jpeg *.bmp *.tif *.tiff"),
    ("Todos los archivos", "*.*"),
]

AUDIO_FILETYPES = [
    ("Audio (WAV/FLAC/OGG/AIFF)", "*.wav *.WAV *.flac *.FLAC *.ogg *.OGG *.oga *.OGA *.aif *.AIF *.aiff *.AIFF"),
    ("Todos los archivos", "*.*"),
]


def _parse_porcentajes(texto: str):
    valores = []
    for p in texto.replace(";", ",").split(","):
        p = p.strip()
        if not p:
            continue
        try:
            v = float(p)
            if 0 < v <= 100:
                valores.append(v)
        except ValueError:
            pass
    return sorted(set(valores))


def _play_audio(wav, fs):
    wav16 = np.int16(np.clip(wav, -1.0, 1.0) * 32767)

    # En Windows usamos winsound porque simpleaudio puede cerrar el proceso
    if os.name == "nt":
        try:
            import threading
            import tempfile
            import wave
            import winsound

            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            tmp_name = tmp.name
            with wave.open(tmp, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)  # 16 bits
                wf.setframerate(int(fs))
                wf.writeframes(wav16.tobytes())
            tmp.close()

            winsound.PlaySound(tmp_name, winsound.SND_FILENAME | winsound.SND_ASYNC)

            class _WinSoundPlayer:
                def __init__(self, path, duration):
                    self._path = path
                    self._timer = threading.Timer(max(0.1, duration + 0.5), self._cleanup)
                    self._timer.daemon = True
                    self._timer.start()

                def _cleanup(self):
                    if self._path:
                        try:
                            os.remove(self._path)
                        except OSError:
                            pass
                        self._path = None

                def stop(self):
                    winsound.PlaySound(None, winsound.SND_PURGE)
                    if self._timer:
                        self._timer.cancel()
                        self._timer = None
                    self._cleanup()

                def __del__(self):
                    if hasattr(self, "_timer") and self._timer:
                        self._timer.cancel()
                    self._cleanup()

            duration = len(wav16) / float(fs) if fs else 0.0
            return _WinSoundPlayer(tmp_name, duration)
        except Exception as e:
            messagebox.showwarning("Audio", f"No se pudo reproducir audio: {e}")
            return None

    # Otros sistemas siguen usando simpleaudio
    try:
        import simpleaudio as sa

        play_obj = sa.play_buffer(wav16, 1, 2, int(fs))
        return play_obj
    except Exception as e:
        messagebox.showwarning("Audio", f"No se pudo reproducir audio: {e}")
        return None


class App(ttk.Window):
    def __init__(self):
        super().__init__(title="Laboratorio 3 - DCT Manual", themename="cosmo", size=(1400, 850))
        self.place_window_center()

        self.modo = tk.StringVar(value="imagen")
        self.ruta_archivo = tk.StringVar(value="")
        self.porcentajes = tk.StringVar(value="5,10,20,50")

        self.fs_audio = None
        self.audio_original = None
        self.audio_rec = {}
        self.audio_play_obj = None
        self.audio_peak = 1.0
        self.audio_len = 0

        self.info_var = tk.StringVar(value="Listo para procesar.")
        self._build_ui()

    # =====================================================================
    # ZOOM (clic izquierdo)
    # =====================================================================
    def _mostrar_zoom(self, titulo, imagen):
        zoom = tk.Toplevel(self)
        zoom.title(titulo)
        zoom.geometry("900x700")

        fig_zoom = plt.Figure(figsize=(8, 6), dpi=100)
        ax = fig_zoom.add_subplot(1, 1, 1)
        ax.imshow(imagen, cmap="gray", aspect="auto")
        ax.axis("off")
        ax.set_title(titulo)

        canvas_zoom = FigureCanvasTkAgg(fig_zoom, master=zoom)
        canvas_zoom.get_tk_widget().pack(fill="both", expand=True)
        canvas_zoom.draw()

    # =====================================================================
    # COMPARACIÓN ORIGINAL VS RECONSTRUIDA (clic derecho)
    # =====================================================================
    def _mostrar_comparacion(self, original, reconstruida, porcentaje, mse):
        win = tk.Toplevel(self)
        win.title(f"Comparación {porcentaje}%  |  MSE={mse:.4f}")
        win.geometry("1300x700")

        fig_cmp = plt.Figure(figsize=(12, 6), dpi=100)

        # Original
        ax1 = fig_cmp.add_subplot(1, 2, 1)
        ax1.imshow(original, cmap="gray", aspect="auto")
        ax1.axis("off")
        ax1.set_title("Original")

        # Reconstruida
        ax2 = fig_cmp.add_subplot(1, 2, 2)
        ax2.imshow(reconstruida, cmap="gray", aspect="auto")
        ax2.axis("off")
        ax2.set_title(f"Reconstruida {porcentaje}%\nMSE={mse:.4f}")

        canvas_cmp = FigureCanvasTkAgg(fig_cmp, master=win)
        canvas_cmp.get_tk_widget().pack(fill="both", expand=True)
        canvas_cmp.draw()

    # =====================================================================
    # INTERFAZ
    # =====================================================================
    def _build_ui(self):
        style = self.style
        style.configure("Title.TLabel", font=("Segoe UI", 18, "bold"))
        style.configure("SubTitle.TLabel", font=("Segoe UI", 11, "italic"))

        header = ttk.Label(
            self,
            text="LABORATORIO 3 - TRANSFORMADA DISCRETA DEL COSENO (DCT)\nCompresión / Descompresión manual (1D / 2D)",
            style="Title.TLabel",
            anchor="center",
            justify="center",
        )
        header.pack(pady=10)

        main_frame = ttk.Frame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=5)

        left_frame = ttk.Labelframe(main_frame, text="Configuración", padding=10)
        left_frame.pack(side="left", fill="y")

        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side="right", fill="both", expand=True)

        self.result_notebook = ttk.Notebook(right_frame)
        self.result_notebook.pack(fill="both", expand=True)

        self.visual_tab = ttk.Frame(self.result_notebook)
        self.result_notebook.add(self.visual_tab, text="Visualizacion")

        # Selección modo
        ttk.Label(left_frame, text="Modo:").grid(row=0, column=0, sticky="w")
        ttk.Radiobutton(left_frame, text="Imagen", variable=self.modo, value="imagen",
                        command=self._on_modo_cambiado).grid(row=0, column=1, sticky="w", padx=5)
        ttk.Radiobutton(left_frame, text="Audio", variable=self.modo, value="audio",
                        command=self._on_modo_cambiado).grid(row=0, column=2, sticky="w", padx=5)

        # Selección archivo
        ttk.Button(left_frame, text="Seleccionar archivo", bootstyle=PRIMARY,
                   command=self._seleccionar_archivo).grid(row=1, column=0, columnspan=3, pady=5, sticky="ew")

        ttk.Label(left_frame, text="Archivo seleccionado:").grid(row=2, column=0, columnspan=3, sticky="w")
        ttk.Label(left_frame, textvariable=self.ruta_archivo, width=40, wraplength=250).grid(
            row=3, column=0, columnspan=3, sticky="w"
        )

        ttk.Separator(left_frame, orient="horizontal").grid(row=4, column=0, columnspan=3, sticky="ew", pady=5)

        # Porcentajes
        ttk.Label(left_frame, text="Retener coeficientes (%):").grid(
            row=5, column=0, columnspan=3, sticky="w"
        )
        ttk.Entry(left_frame, textvariable=self.porcentajes, width=25).grid(
            row=6, column=0, columnspan=3, sticky="ew", pady=2
        )
        ttk.Label(left_frame, text="Ejemplo: 5,10,20,50").grid(row=7, column=0, columnspan=3, sticky="w")

        ttk.Button(left_frame, text="Procesar", bootstyle=SUCCESS, command=self._procesar).grid(
            row=8, column=0, columnspan=3, pady=8, sticky="ew"
        )

        ttk.Separator(left_frame, orient="horizontal").grid(row=9, column=0, columnspan=3, sticky="ew", pady=5)

        # Controles de audio
        ttk.Label(left_frame, text="Controles de audio:", style="SubTitle.TLabel").grid(
            row=10, column=0, columnspan=3, sticky="w", pady=(5, 2)
        )
        self.audio_controls = ttk.Frame(left_frame)
        self.audio_controls.grid(row=11, column=0, columnspan=3, sticky="ew")

        ttk.Separator(left_frame, orient="horizontal").grid(row=12, column=0, columnspan=3, sticky="ew", pady=5)

        # Información
        ttk.Label(left_frame, text="Información:", style="SubTitle.TLabel").grid(
            row=13, column=0, columnspan=3, sticky="w"
        )
        ttk.Label(left_frame, textvariable=self.info_var, wraplength=260, justify="left").grid(
            row=14, column=0, columnspan=3, sticky="w", pady=(2, 0)
        )

        # Figura principal (tab Visualizacion)
        self.fig = plt.Figure(figsize=(20, 10), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.visual_tab)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        self.audio_tabs = []
        self.audio_tab_lookup = {}

        # Footer
        ttk.Label(self, text="Desarrollado por: Diego Alejandro Machado Tovar",
                  style="SubTitle.TLabel").pack(side="bottom", pady=5)

        self._refresh_audio_controls(clear=True)
        self.audio_placeholder = None
        self._show_audio_placeholder()

    # =====================================================================
    # GESTIÓN DE PESTAÑAS DE AUDIO
    # =====================================================================
    def _show_audio_placeholder(self):
        self._remove_audio_placeholder()
        placeholder = ttk.Frame(self.result_notebook)
        ttk.Label(
            placeholder,
            text="Las senales procesadas en modo audio apareceran aqui.",
            justify="center",
            padding=20,
        ).pack(expand=True, fill="both")
        self.result_notebook.add(placeholder, text="Senales")
        self.audio_placeholder = placeholder

    def _remove_audio_placeholder(self):
        if self.audio_placeholder is not None:
            try:
                self.result_notebook.forget(self.audio_placeholder)
            except tk.TclError:
                pass
            self.audio_placeholder = None

    def _clear_audio_tabs(self, keep_placeholder=False):
        for frame in self.audio_tabs:
            try:
                self.result_notebook.forget(frame)
            except tk.TclError:
                pass
        self.audio_tabs.clear()
        self.audio_tab_lookup = {}
        if not keep_placeholder:
            self._show_audio_placeholder()

    def _add_audio_tab(self, titulo, datos, info_text, fs, referencia=None):
        self._remove_audio_placeholder()
        frame = ttk.Frame(self.result_notebook)
        ttk.Label(frame, text=info_text).pack(anchor="w", padx=10, pady=(8, 0))
        datos_np = np.asarray(datos, dtype=float)

        fig = plt.Figure(figsize=(8, 3), dpi=100)
        ax = fig.add_subplot(1, 1, 1)
        referencia_np = np.asarray(referencia, dtype=float) if referencia is not None else None
        self._draw_waveform_plot(ax, datos_np, titulo, fs, referencia_np)
        fig.tight_layout()

        tab_canvas = FigureCanvasTkAgg(fig, master=frame)
        tab_canvas.draw()
        tab_canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

        self.result_notebook.add(frame, text=titulo)
        self.audio_tabs.append(frame)
        self.audio_tab_lookup[titulo] = frame

    def _focus_audio_tab(self, titulo):
        frame = self.audio_tab_lookup.get(titulo)
        if frame is not None:
            try:
                self.result_notebook.select(frame)
            except tk.TclError:
                pass

    def _draw_waveform_plot(self, ax, datos, titulo, fs=None, referencia=None):
        arr = np.asarray(datos, dtype=float)
        arr = np.nan_to_num(arr, nan=0.0)
        if arr.size < 2:
            ax.text(0.5, 0.5, "Sin datos", ha="center", va="center", transform=ax.transAxes)
            ax.set_axis_off()
            return

        total_len = max(self.audio_len, arr.size)

        if fs and fs > 0:
            duration = (total_len - 1) / fs
            x_limit = duration
            x = np.linspace(0, duration, arr.size)
            ax.set_xlabel("Tiempo (s)")
            ax.set_xlim(0, duration)
        else:
            duration = None
            x_limit = total_len - 1
            x = np.linspace(0, x_limit, arr.size)
            ax.set_xlabel("Muestra")
            ax.set_xlim(0, x_limit)

        if referencia is not None:
            ref = np.asarray(referencia, dtype=float)
            ref = np.nan_to_num(ref, nan=0.0)
            ref_x = np.linspace(0, x_limit, ref.size)
            ax.plot(ref_x, ref, color="#999999", linewidth=0.8, alpha=0.7, label="Original")

        ax.plot(x, arr, color="#1f77b4", linewidth=0.9)
        ax.fill_between(x, arr, 0, color="#1f77b4", alpha=0.15)
        ax.axhline(0.0, color="#666666", linestyle="--", linewidth=0.7)
        ax.set_ylim(-1.05, 1.05)
        ax.set_title(f"Forma de onda - {titulo}")
        ax.set_ylabel("Amplitud normalizada")
        ax.grid(True, alpha=0.25)
        if referencia is not None:
            ax.legend(loc="upper right", fontsize=8)

    def _plot_audio_overview(self, series, fs):
        self.fig.clear()
        if not series:
            self.canvas.draw()
            return

        ax = self.fig.add_subplot(1, 1, 1)
        max_len = self.audio_len or max(len(np.asarray(datos, dtype=float)) for _, datos, _ in series if len(np.asarray(datos)) > 0)
        if max_len == 0:
            self.canvas.draw()
            return

        max_samples = 8000
        sample_count = min(max_samples, max_len)
        use_time = fs and fs > 0
        if use_time:
            duration = (self.audio_len - 1) / fs if self.audio_len else sample_count / fs
            x_axis = np.linspace(0, duration, sample_count)
            ax.set_xlabel("Tiempo (s)")
        else:
            end = self.audio_len - 1 if self.audio_len else sample_count - 1
            x_axis = np.linspace(0, end, sample_count)
            ax.set_xlabel("Muestra")

        ref_max = self.audio_peak if self.audio_peak and self.audio_peak > 0 else 1.0

        colors = plt.cm.tab10.colors
        for series_idx, (label, datos, _) in enumerate(series):
            arr = np.asarray(datos, dtype=float)
            n = arr.size
            if n == 0:
                continue
            if n > sample_count:
                down_idx = np.linspace(0, n - 1, sample_count).astype(int)
                tramo = arr[down_idx]
                x_vals = x_axis
            else:
                tramo = arr
                proportion = tramo.size / sample_count
                x_vals = x_axis[:tramo.size]
            tramo = np.nan_to_num(tramo, nan=0.0)
            if tramo.size < 2:
                continue
            tramo = tramo / ref_max
            ax.plot(
                x_vals[:tramo.size],
                tramo,
                label=label,
                linewidth=1.0,
                alpha=0.9,
                color=colors[series_idx % len(colors)],
            )

        ax.set_ylim(-1.2, 1.2)
        if use_time:
            titulo = "Comparacion de senales (escala temporal completa)"
        else:
            titulo = "Comparacion de senales (escala de muestras completa)"
        ax.set_title(titulo)
        ax.legend(loc="upper right", fontsize=8)
        ax.grid(True, alpha=0.3)
        self.fig.tight_layout()
        self.canvas.draw()

    # =====================================================================
    # CAMBIO DE MODO
    # =====================================================================
    def _on_modo_cambiado(self):
        self._refresh_audio_controls(clear=(self.modo.get() != "audio"))
        self._clear_audio_tabs()

    # =====================================================================
    # SELECCIONAR ARCHIVO (CORREGIDO)
    # =====================================================================
    def _seleccionar_archivo(self):
        if self.modo.get() == "imagen":
            dialog_title = "Seleccionar imagen"
            dialog_types = IMG_FILETYPES + AUDIO_FILETYPES
        else:
            dialog_title = "Seleccionar archivo de audio"
            dialog_types = AUDIO_FILETYPES + IMG_FILETYPES

        ruta = filedialog.askopenfilename(title=dialog_title, filetypes=dialog_types)

        if ruta:
            self.ruta_archivo.set(ruta)
            self.info_var.set("Archivo seleccionado correctamente.")

    # =====================================================================
    # PROCESAMIENTO PRINCIPAL
    # =====================================================================
    def _procesar(self):
        porcentajes = _parse_porcentajes(self.porcentajes.get())
        if not porcentajes:
            messagebox.showwarning("Porcentajes", "Ingrese porcentajes válidos.")
            return
        if not self.ruta_archivo.get():
            messagebox.showwarning("Archivo", "Seleccione un archivo primero.")
            return

        if self.modo.get() == "imagen":
            self._procesar_imagen(porcentajes)
            self._refresh_audio_controls(clear=True)
        else:
            self._procesar_audio(porcentajes)
            self._refresh_audio_controls(clear=False)

    # =====================================================================
    # PROCESAMIENTO DE IMAGEN (DCT 2D + GRILLA DINÁMICA + ZOOM + COMPARACIÓN)
    # =====================================================================
    def _procesar_imagen(self, porcentajes):
        try:
            self._clear_audio_tabs()
            ruta = self.ruta_archivo.get()
            img = _leer_imagen_grises(ruta)
            if img is None:
                raise FileNotFoundError("No se pudo leer la imagen")

            h, w = img.shape
            b = 8

            pad_h = (b - (h % b)) % b
            pad_w = (b - (w % b)) % b
            img_pad = np.pad(img, ((0, pad_h), (0, pad_w)), mode="edge") if (pad_h or pad_w) else img

            dct_img = aplicar_dct_por_bloques(img_pad, tamano_bloque=b)

            total_imgs = 2 + len(porcentajes)
            ncols = 3
            nrows = int(np.ceil(total_imgs / ncols))

            self.fig.clear()
            idx = 1
            info = []

            ax = self.fig.add_subplot(nrows, ncols, idx)
            ax.imshow(img, cmap="gray", aspect="auto")
            ax.axis("off")
            ax.set_title("Original")
            idx += 1

            ax = self.fig.add_subplot(nrows, ncols, idx)
            ax.imshow(np.log1p(np.abs(dct_img)), cmap="inferno", aspect="auto")
            ax.axis("off")
            ax.set_title("Mapa |DCT| (log)")
            idx += 1

            for p in porcentajes:
                total = dct_img.size
                k = max(1, min(total, int((p / 100.0) * total)))

                plano = dct_img.flatten()
                idxs_sorted = np.argsort(np.abs(plano))[::-1]
                pf = np.zeros_like(plano)
                pf[idxs_sorted[:k]] = plano[idxs_sorted[:k]]
                dct_filtrada = pf.reshape(dct_img.shape)

                rec_pad = aplicar_idct_por_bloques(dct_filtrada, tamano_bloque=b)
                rec = rec_pad[:h, :w]

                mse = float(np.mean((img.astype(np.float32) - rec.astype(np.float32)) ** 2))
                info.append(f"{p}% → MSE={mse:.6f}")

                ax = self.fig.add_subplot(nrows, ncols, idx)
                ax.imshow(rec, cmap="gray", aspect="auto")
                ax.axis("off")
                ax.set_title(f"Rec {p}%\nMSE={mse:.3f}")

                def on_click(event, p=p, rec_img=rec, orig_img=img, mse_val=mse, ax_ref=ax):
                    if event.inaxes != ax_ref:
                        return
                    if event.button == 1:
                        self._mostrar_zoom(f"Zoom {p}%", rec_img)
                    elif event.button == 3:
                        self._mostrar_comparacion(orig_img, rec_img, p, mse_val)

                self.canvas.mpl_connect("button_press_event", on_click)

                idx += 1

            self.fig.subplots_adjust(wspace=0.25, hspace=0.35)
            self.canvas.draw()

            self.info_var.set("Procesamiento de imagen:\n" + "\n".join(info))

        except Exception as e:
            messagebox.showerror("Imagen", str(e))

    # =====================================================================
    # PROCESAMIENTO DE AUDIO (DCT 1D)
    # =====================================================================
    def _procesar_audio(self, porcentajes):
        try:
            import soundfile as sf

            ruta = self.ruta_archivo.get()
            senal, fs = sf.read(ruta)

            if hasattr(senal, "ndim") and senal.ndim > 1:
                senal = senal.mean(axis=1)

            maxabs = float(np.max(np.abs(senal)))
            senal_norm = senal / maxabs if maxabs > 0 else senal

            coef = np.array(transformada_dct(senal_norm.tolist()), dtype=float)

            self.audio_original = senal_norm
            self.fs_audio = fs
            self.audio_rec = {}
            self._clear_audio_tabs(keep_placeholder=True)
            self.audio_peak = float(np.max(np.abs(senal_norm))) if np.max(np.abs(senal_norm)) > 0 else 1.0
            self.audio_len = len(senal_norm)

            total = len(coef)
            idxs = np.argsort(np.abs(coef))[::-1]
            info = []
            tab_data = []
            duracion = (len(senal_norm) / fs) if fs else 0.0

            tab_data.append(
                (
                    "Original",
                    senal_norm,
                    f"Fs: {fs} Hz | Duracion: {duracion:.2f} s",
                )
            )

            for i, p in enumerate(porcentajes):
                k = max(1, min(total, int((p / 100.0) * total)))
                mask = np.zeros_like(coef)
                mask[idxs[:k]] = coef[idxs[:k]]

                rec = np.array(transformada_idct(mask.tolist()), dtype=float)
                label = f"{p:g}"
                self.audio_rec[label] = rec

                mse = float(np.mean((senal_norm - rec) ** 2))
                info.append(f"{p}% ��' MSE={mse:.6f}")
                tab_data.append(
                    (
                        f"Rec {p:g}%",
                        rec,
                        f"Fs: {fs} Hz | Duracion: {duracion:.2f} s | MSE={mse:.6f}",
                    )
                )

            self._plot_audio_overview(tab_data, fs)

            for titulo, data, extra in tab_data:
                referencia = None if titulo == "Original" else self.audio_original
                self._add_audio_tab(titulo, data, extra, fs, referencia)
            self._focus_audio_tab("Original")

            self.info_var.set("Procesamiento de audio:\n" + "\n".join(info))

        except Exception as e:
            messagebox.showerror("Audio", str(e))

    # =====================================================================
    # CONTROLES DE AUDIO
    # =====================================================================
    def _refresh_audio_controls(self, clear=False):
        for w in self.audio_controls.winfo_children():
            w.destroy()

        if clear or self.modo.get() != "audio":
            ttk.Label(self.audio_controls, text="(Modo audio)").pack(anchor="w")
            return

        def stop():
            if self.audio_play_obj is not None:
                try:
                    self.audio_play_obj.stop()
                except Exception:
                    pass

        def play_orig():
            stop()
            if self.audio_original is not None and self.fs_audio:
                self.audio_play_obj = _play_audio(self.audio_original, self.fs_audio)
                self._focus_audio_tab("Original")

        ttk.Button(self.audio_controls, text="Reproducir original", bootstyle=INFO,
                   command=play_orig).pack(fill="x", pady=2)

        def sort_key(label):
            try:
                return float(label)
            except (TypeError, ValueError):
                return float("inf")

        for label in sorted(self.audio_rec.keys(), key=sort_key):
            def make_cb(name=label):
                def _cb():
                    stop()
                    data = self.audio_rec.get(name)
                    if data is not None and self.fs_audio:
                        self.audio_play_obj = _play_audio(data, self.fs_audio)
                        self._focus_audio_tab(f"Rec {name}%")
                return _cb

            ttk.Button(self.audio_controls, text=f"Reproducir {label}%", bootstyle=SUCCESS,
                       command=make_cb()).pack(fill="x", pady=2)


def iniciar_interfaz():
    app = App()
    app.mainloop()




