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
    try:
        import simpleaudio as sa
        wav16 = np.int16(np.clip(wav, -1.0, 1.0) * 32767)
        play_obj = sa.play_buffer(wav16, 1, 2, fs)
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

        # Figura
        self.fig = plt.Figure(figsize=(20, 10), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=right_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        # Footer
        ttk.Label(self, text="Desarrollado por: Diego Alejandro Machado Tovar",
                  style="SubTitle.TLabel").pack(side="bottom", pady=5)

        self._refresh_audio_controls(clear=True)

    def _on_modo_cambiado(self):
        self._refresh_audio_controls(clear=(self.modo.get() != "audio"))

    def _seleccionar_archivo(self):
        if self.modo.get() == "imagen":
            ruta = filedialog.askopenfilename(
                filetypes=[("Imágenes", ("*.png", "*.jpg", "*.jpeg", "*.bmp", "*.tif", "*.tiff"))]
            )
        else:
            ruta = filedialog.askopenfilename(filetypes=[("Archivos WAV", "*.wav")])

        if ruta:
            self.ruta_archivo.set(ruta)
            self.info_var.set("Archivo seleccionado.")

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
    # ⭐ PROCESAMIENTO DE IMAGEN CON GRILLA DINÁMICA + ZOOM + COMPARACIÓN
    # =====================================================================
    def _procesar_imagen(self, porcentajes):
        try:
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

            # ---------------------------------------------------------------
            # ⭐ GRILLA DINÁMICA
            # ---------------------------------------------------------------
            total_imgs = 2 + len(porcentajes)
            ncols = 3
            nrows = int(np.ceil(total_imgs / ncols))

            self.fig.clear()
            idx = 1
            info = []

            # -------------------------
            # ORIGINAL
            # -------------------------
            ax = self.fig.add_subplot(nrows, ncols, idx)
            ax.imshow(img, cmap="gray", aspect="auto")
            ax.axis("off")
            ax.set_title("Original")
            idx += 1

            # -------------------------
            # MAPA DCT
            # -------------------------
            ax = self.fig.add_subplot(nrows, ncols, idx)
            ax.imshow(np.log1p(np.abs(dct_img)), cmap="inferno", aspect="auto")
            ax.axis("off")
            ax.set_title("Mapa |DCT| (log)")
            idx += 1

            # -------------------------
            # RECONSTRUCCIONES
            # -------------------------
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

                # -----------------------------
                # ⭐ EVENTOS DE CLIC
                # -----------------------------
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
    # AUDIO (inalterado salvo interfaz)
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

            self.fig.clear()
            ax = self.fig.add_subplot(1, 1, 1)
            ax.plot(senal_norm, label="Original", color="k", linewidth=0.8)

            total = len(coef)
            idxs = np.argsort(np.abs(coef))[::-1]
            colors = plt.cm.tab10.colors
            info = []

            for i, p in enumerate(porcentajes):
                k = max(1, min(total, int((p / 100.0) * total)))
                mask = np.zeros_like(coef)
                mask[idxs[:k]] = coef[idxs[:k]]

                rec = np.array(transformada_idct(mask.tolist()), dtype=float)
                self.audio_rec[int(p)] = rec

                mse = float(np.mean((senal_norm - rec) ** 2))
                info.append(f"{p}% → MSE={mse:.6f}")

                ax.plot(rec, label=f"Rec {p}%", color=colors[i % len(colors)], alpha=0.8, linewidth=0.8)

            ax.set_title("Señal de voz")
            ax.legend(loc="upper right", fontsize=8)
            self.fig.tight_layout()
            self.canvas.draw()

            self.info_var.set("Procesamiento de audio:\n" + "\n".join(info))

        except Exception as e:
            messagebox.showerror("Audio", str(e))

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

        ttk.Button(self.audio_controls, text="Reproducir original", bootstyle=INFO,
                   command=play_orig).pack(fill="x", pady=2)

        for p in sorted(self.audio_rec.keys()):
            def make_cb(pp=p):
                def _cb():
                    stop()
                    self.audio_play_obj = _play_audio(self.audio_rec[pp], self.fs_audio)
                return _cb

            ttk.Button(self.audio_controls, text=f"Reproducir {p}%", bootstyle=SUCCESS,
                       command=make_cb()).pack(fill="x", pady=2)


def iniciar_interfaz():
    app = App()
    app.mainloop()
