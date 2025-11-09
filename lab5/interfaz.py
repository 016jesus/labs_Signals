import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import filedialog, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import numpy as np
import os

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
        super().__init__(title="Laboratorio 3 - DCT Manual", themename="cosmo", size=(1100, 750))
        self.place_window_center()

        self.modo = tk.StringVar(value="imagen")
        self.ruta_archivo = tk.StringVar(value="")
        self.porcentajes = tk.StringVar(value="5,10,20,50")
        self.fs_audio = None
        self.audio_original = None
        self.audio_rec = {}
        self.audio_play_obj = None

        self._build_ui()

    def _build_ui(self):
        header = ttk.Label(self, text=(
            "LABORATORIO 3 - DCT MANUAL\n"
            "Compresion/Descompresion por DCT (1D/2D)"
        ), font=("Segoe UI", 16, "bold"), anchor="center")
        header.pack(pady=10)

        controls = ttk.Frame(self)
        controls.pack(fill="x", padx=10)

        ttk.Label(controls, text="Modo:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ttk.Radiobutton(controls, text="Imagen", variable=self.modo, value="imagen").grid(row=0, column=1, padx=5)
        ttk.Radiobutton(controls, text="Audio", variable=self.modo, value="audio").grid(row=0, column=2, padx=5)

        ttk.Button(controls, text="Seleccionar archivo", bootstyle=PRIMARY, command=self._seleccionar_archivo).grid(row=0, column=3, padx=10)
        ttk.Label(controls, textvariable=self.ruta_archivo, width=70, anchor="w").grid(row=0, column=4, padx=5, sticky="w")

        ttk.Label(controls, text="Porcentajes (%):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(controls, textvariable=self.porcentajes, width=30).grid(row=1, column=1, columnspan=2, padx=5, sticky="w")
        ttk.Button(controls, text="Procesar", bootstyle=SUCCESS, command=self._procesar).grid(row=1, column=3, padx=10)

        self.fig = plt.Figure(figsize=(9, 5.5), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

        self.audio_controls = ttk.Frame(self)
        self.audio_controls.pack(fill="x", padx=10, pady=5)
        self._refresh_audio_controls()

        ttk.Label(self, text="Desarrollado por: Diego Alejandro Machado Tovar", font=("Segoe UI", 9, "italic")).pack(side="bottom", pady=5)

    def _seleccionar_archivo(self):
        if self.modo.get() == "imagen":
            ruta = filedialog.askopenfilename(filetypes=[("Imagenes", ("*.png", "*.jpg", "*.jpeg", "*.bmp", "*.tif", "*.tiff"))])
        else:
            ruta = filedialog.askopenfilename(filetypes=[("WAV", "*.wav")])
        if ruta:
            self.ruta_archivo.set(ruta)

    def _procesar(self):
        porcentajes = _parse_porcentajes(self.porcentajes.get())
        if len(porcentajes) < 3:
            messagebox.showwarning("Porcentajes", "Ingrese al menos 3 porcentajes validos, separados por coma.")
            return
        if not self.ruta_archivo.get():
            messagebox.showwarning("Archivo", "Seleccione un archivo primero.")
            return

        if self.modo.get() == "imagen":
            self._procesar_imagen(porcentajes)
            self._refresh_audio_controls(clear=True)
        else:
            self._procesar_audio(porcentajes)
            self._refresh_audio_controls()

    def _procesar_imagen(self, porcentajes):
        try:
            img = _leer_imagen_grises(self.ruta_archivo.get())
            if img is None:
                raise FileNotFoundError("No se pudo leer la imagen")
            h, w = img.shape
            b = 8
            pad_h = (b - (h % b)) % b
            pad_w = (b - (w % b)) % b
            img_pad = np.pad(img, ((0, pad_h), (0, pad_w)), mode="edge") if (pad_h or pad_w) else img
            dct_img = aplicar_dct_por_bloques(img_pad, tamano_bloque=b)

            ncols = 1 + len(porcentajes)
            self.fig.clear()
            for idx in range(ncols):
                ax = self.fig.add_subplot(1, ncols, idx + 1)
                ax.axis('off')
                if idx == 0:
                    ax.imshow(img, cmap='gray')
                    ax.set_title("Original")
                else:
                    p = porcentajes[idx - 1]
                    total = dct_img.size
                    k = max(1, min(total, int((p / 100.0) * total)))
                    plano = dct_img.flatten()
                    idxs = np.argsort(np.abs(plano))[::-1]
                    pf = np.zeros_like(plano)
                    pf[idxs[:k]] = plano[idxs[:k]]
                    dct_f = pf.reshape(dct_img.shape)
                    rec_pad = aplicar_idct_por_bloques(dct_f, tamano_bloque=b)
                    rec = rec_pad[:h, :w]
                    ax.imshow(rec, cmap='gray')
                    ax.set_title(f"Rec {int(p)}%")
            self.fig.tight_layout()
            self.canvas.draw()
        except Exception as e:
            messagebox.showerror("Imagen", f"Error procesando imagen:\n{e}")

    def _procesar_audio(self, porcentajes):
        try:
            import soundfile as sf
            senal, fs = sf.read(self.ruta_archivo.get())
            if hasattr(senal, 'ndim') and senal.ndim > 1:
                senal = senal.mean(axis=1)
            maxabs = np.max(np.abs(senal))
            if maxabs > 0:
                senal = senal / maxabs

            coef = transformada_dct(senal)
            self.audio_original = senal
            self.fs_audio = fs
            self.audio_rec = {}

            self.fig.clear()
            ax = self.fig.add_subplot(1, 1, 1)
            ax.plot(senal, label='Original', color='k', linewidth=1)

            total = len(coef)
            idxs = np.argsort(np.abs(coef))[::-1]
            colors = plt.cm.tab10.colors
            for i, p in enumerate(porcentajes):
                k = max(1, min(total, int((p / 100.0) * total)))
                mask = np.zeros_like(coef)
                mask[idxs[:k]] = coef[idxs[:k]]
                rec = transformada_idct(mask)
                self.audio_rec[int(p)] = rec
                ax.plot(rec, label=f'Rec {int(p)}% ', color=colors[i % len(colors)], alpha=0.8)

            ax.set_title('Senal de voz (dominio del tiempo)')
            ax.legend(loc='upper right', fontsize=8)
            self.fig.tight_layout()
            self.canvas.draw()
        except Exception as e:
            messagebox.showerror("Audio", f"Error procesando audio:\n{e}")

    def _refresh_audio_controls(self, clear=False):
        for w in self.audio_controls.winfo_children():
            w.destroy()

        if clear or self.modo.get() != 'audio':
            ttk.Label(self.audio_controls, text="").pack()
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

        ttk.Button(self.audio_controls, text='Reproducir Original', bootstyle=INFO, command=play_orig).pack(side='left', padx=5)

        for p in sorted(self.audio_rec.keys()):
            def make_cb(pp=p):
                def _cb():
                    stop()
                    self.audio_play_obj = _play_audio(self.audio_rec[pp], self.fs_audio)
                return _cb
            ttk.Button(self.audio_controls, text=f'Reproducir {p}%', bootstyle=SUCCESS, command=make_cb()).pack(side='left', padx=5)


def iniciar_interfaz():
    app = App()
    app.mainloop()

