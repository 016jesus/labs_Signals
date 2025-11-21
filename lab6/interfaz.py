import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import filedialog, messagebox

import math
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

from procesador_imagen_dct import (
    leer_imagen_grises,
    aplicar_dct_bloques,
    aplicar_idct_bloques,
    filtrar_coeficientes_pequenos_imagen,
)

from procesador_audio_dct import (
    cargar_audio,
    dct_audio,
    idct_audio,
    filtrar_coeficientes_pequenos_audio,
)


class AplicacionDCT(ttk.Window):
    def __init__(self):
        super().__init__(title="Laboratorio 3 — Aplicación DCT 1D / 2D", themename="cosmo", size=(1600, 1000))
        self.place_window_center()

        self.modo = tk.StringVar(value="imagen")
        self.ruta_archivo = tk.StringVar(value="")
        self.porcentajes = tk.StringVar(value="1,2,3,5")

        self.audio_fs = None
        self.audio_original = None
        try:
            import sounddevice as sd  # type: ignore
            self._sd = sd
        except Exception:
            self._sd = None

        self._construir_ui()

    def _construir_ui(self):
        header = ttk.Label(self,
            text="LABORATORIO 3 — APLICACIÓN COMPUTACIONAL CON DCT 1D / 2D",
            font=("Segoe UI", 18, "bold"),
            anchor="center")
        header.pack(pady=10)

        marco_principal = ttk.Frame(self)
        marco_principal.pack(fill="both", expand=True, padx=10, pady=5)

        panel = ttk.Labelframe(marco_principal, text="Configuración", padding=10, width=300)
        panel.pack(side="left", fill="y", padx=(0, 10))
        panel.pack_propagate(False)

        ttk.Label(panel, text="Modo de operación:").grid(row=0, column=0, sticky="w")
        ttk.Radiobutton(panel, text="Imagen", variable=self.modo, value="imagen").grid(row=0, column=1, sticky="w")
        ttk.Radiobutton(panel, text="Audio", variable=self.modo, value="audio").grid(row=0, column=2, sticky="w")

        ttk.Button(panel, text="Seleccionar archivo", bootstyle=PRIMARY,
                   command=self._seleccionar_archivo).grid(row=1, column=0, columnspan=3, pady=5, sticky="ew")

        ttk.Label(panel, textvariable=self.ruta_archivo, wraplength=250).grid(row=2, column=0, columnspan=3, sticky="w")

        ttk.Separator(panel).grid(row=3, column=0, columnspan=3, pady=5, sticky="ew")

        ttk.Label(panel, text="Porcentajes (% a eliminar):").grid(row=4, column=0, sticky="w")
        ttk.Entry(panel, textvariable=self.porcentajes).grid(row=5, column=0, columnspan=3, sticky="ew")
        ttk.Label(panel, text="Ej: 1,2,5,10 (mínimo 3 valores)").grid(row=6, column=0, columnspan=3, sticky="w")

        ttk.Button(panel, text="Procesar", bootstyle=SUCCESS,
                   command=self._procesar).grid(row=7, column=0, columnspan=3, pady=10, sticky="ew")

        self.notebook = ttk.Notebook(marco_principal)
        self.notebook.pack(side="right", fill="both", expand=True)

        self._crear_tab_resumen_inicial()

    def _crear_tab_resumen_inicial(self):
        """Muestra un mensaje inicial mientras no hay resultados."""
        frame = ttk.Frame(self.notebook)
        ttk.Label(frame, text="Seleccione un archivo y presione Procesar.", anchor="center").pack(
            expand=True, fill="both", padx=10, pady=10
        )
        self.notebook.add(frame, text="Resumen general")

    def _seleccionar_archivo(self):
        tipos = [
            ("Imágenes", "*.jpg;*.png;*.jpeg;*.bmp"),
            ("Audio WAV", "*.wav"),
            ("Todos los archivos", "*.*")
        ]
        ruta = filedialog.askopenfilename(title="Seleccionar archivo", filetypes=tipos)
        if ruta:
            self.ruta_archivo.set(ruta)

    def _procesar(self):
        ruta = self.ruta_archivo.get()
        if ruta == "":
            messagebox.showerror("Error", "Seleccione un archivo primero.")
            return

        porcentajes = self._parsear_porcentajes()

        if not porcentajes or len(porcentajes) < 3:
            messagebox.showerror("Error", "Ingrese al menos 3 porcentajes válidos entre 0 y 100 (ej: 1, 2.5, 5).")
            return

        self._limpiar_tabs()

        if self.modo.get() == "imagen":
            self._procesar_imagen(porcentajes)
        else:
            self._procesar_audio(porcentajes)

    def _parsear_porcentajes(self):
        valores = []
        for p in self.porcentajes.get().replace(";", ",").split(","):
            p = p.strip()
            if p == "":
                continue
            try:
                valor = float(p)
            except ValueError:
                continue
            if 0 <= valor <= 100:
                valores.append(valor)
        return valores

    def _limpiar_tabs(self):
        """Elimina completamente las pestañas existentes para evitar fugas de memoria."""
        self._stop_audio()
        for tab_id in self.notebook.tabs():
            widget = self.notebook.nametowidget(tab_id)
            widget.destroy()

    def _procesar_imagen(self, porcentajes):
        img = leer_imagen_grises(self.ruta_archivo.get())
        if img is None:
            messagebox.showerror("Error", "No se pudo leer la imagen.")
            return

        dct_total, shape_original = aplicar_dct_bloques(img)

        reconstrucciones = []
        for p in porcentajes:
            dct_filtrada = filtrar_coeficientes_pequenos_imagen(dct_total, p)
            rec = aplicar_idct_bloques(dct_filtrada, original_shape=shape_original)
            reconstrucciones.append((p, dct_filtrada, rec))

        # Tab de resumen
        resumen = ttk.Frame(self.notebook)
        self.notebook.add(resumen, text="Resumen general")
        
        resumen_fig = Figure(figsize=(14, 7), dpi=100)
        ax0 = resumen_fig.add_subplot(1, 2, 1)
        ax0.imshow(img, cmap="gray", interpolation='nearest')
        ax0.set_title("Imagen original", fontsize=14, fontweight='bold')
        ax0.axis("on")
        ax0.grid(True, alpha=0.3)

        ax1 = resumen_fig.add_subplot(1, 2, 2)
        ax1.imshow(np.log1p(np.abs(dct_total)), cmap="inferno", interpolation='nearest')
        ax1.set_title("Mapa DCT completa (log)", fontsize=14, fontweight='bold')
        ax1.axis("on")
        ax1.grid(True, alpha=0.3)

        resumen_fig.tight_layout()
        resumen_canvas = FigureCanvasTkAgg(resumen_fig, resumen)
        resumen_canvas.draw()
        
        # Agregar toolbar con zoom y paneo
        toolbar_frame = ttk.Frame(resumen)
        toolbar_frame.pack(side="top", fill="x")
        toolbar = NavigationToolbar2Tk(resumen_canvas, toolbar_frame)
        toolbar.update()
        
        resumen_canvas.get_tk_widget().pack(side="top", fill="both", expand=True)

        # Tabs individuales para cada porcentaje
        for p, dct_filtrada, rec in reconstrucciones:
            k = f"Imagen {p}%"
            tab = ttk.Frame(self.notebook)
            self.notebook.add(tab, text=k)

            fig = Figure(figsize=(14, 10), dpi=100)
            ax1 = fig.add_subplot(2, 2, 1)
            ax2 = fig.add_subplot(2, 2, 2)
            ax3 = fig.add_subplot(2, 2, 3)
            ax4 = fig.add_subplot(2, 2, 4)

            ax1.imshow(img, cmap="gray", interpolation='nearest')
            ax1.set_title("Imagen original", fontsize=12, fontweight='bold')
            ax1.axis("on")
            ax1.grid(True, alpha=0.3)

            ax2.imshow(rec, cmap="gray", interpolation='nearest')
            ax2.set_title(f"Reconstruida ({p}% coef. eliminados)", fontsize=12, fontweight='bold')
            ax2.axis("on")
            ax2.grid(True, alpha=0.3)

            ax3.imshow(np.log1p(np.abs(dct_filtrada)), cmap="inferno", interpolation='nearest')
            ax3.set_title("Mapa DCT filtrada (log)", fontsize=12, fontweight='bold')
            ax3.axis("on")
            ax3.grid(True, alpha=0.3)

            # Diferencia absoluta
            diff = np.abs(img.astype(float) - rec.astype(float))
            im4 = ax4.imshow(diff, cmap="hot", interpolation='nearest')
            ax4.set_title("Diferencia absoluta |Original - Reconstruida|", fontsize=12, fontweight='bold')
            ax4.axis("on")
            ax4.grid(True, alpha=0.3)
            fig.colorbar(im4, ax=ax4, fraction=0.046, pad=0.04)

            fig.tight_layout()
            fig_canvas = FigureCanvasTkAgg(fig, master=tab)
            fig_canvas.draw()
            
            # Agregar toolbar con zoom y paneo
            toolbar_frame = ttk.Frame(tab)
            toolbar_frame.pack(side="top", fill="x")
            toolbar = NavigationToolbar2Tk(fig_canvas, toolbar_frame)
            toolbar.update()
            
            fig_canvas.get_tk_widget().pack(side="top", fill="both", expand=True)

    def _procesar_audio(self, porcentajes):
        try:
            senal, fs = cargar_audio(self.ruta_archivo.get())
        except Exception as exc:
            messagebox.showerror("Error", f"No se pudo leer el audio: {exc}")
            return

        if senal is None or len(senal) == 0:
            messagebox.showerror("Error", "El archivo de audio está vacío o no es válido.")
            return

        self.audio_fs = fs
        self.audio_original = senal

        coef = dct_audio(senal)

        reconstrucciones = []
        for p in porcentajes:
            coef_f = filtrar_coeficientes_pequenos_audio(coef, p)
            rec = idct_audio(coef_f)
            reconstrucciones.append((p, rec))

        resumen = ttk.Frame(self.notebook)
        self.notebook.add(resumen, text="Resumen audio")
        controles_resumen = ttk.Frame(resumen)
        controles_resumen.pack(side="top", fill="x", padx=10, pady=5)
        ttk.Button(controles_resumen, text="Reproducir original",
                   command=lambda s=senal: self._play_audio(s, fs)).pack(side="left", padx=5)
        for p, rec in reconstrucciones:
            ttk.Button(controles_resumen, text=f"Reproducir {p}%",
                       command=lambda r=rec: self._play_audio(r, fs)).pack(side="left", padx=5)
        ttk.Button(controles_resumen, text="Detener",
                   command=self._stop_audio).pack(side="left", padx=5)

        fig_resumen = plt.Figure(figsize=(10, 4))
        ax_res = fig_resumen.add_subplot(1, 1, 1)
        ax_res.plot(senal, label="Original")
        for p, rec in reconstrucciones:
            ax_res.plot(rec, label=f"{p}%")
        ax_res.legend()
        resumen_canvas = FigureCanvasTkAgg(fig_resumen, master=resumen)
        resumen_canvas.draw()
        resumen_canvas.get_tk_widget().pack(side="top", fill="both", expand=True)

        for p, rec in reconstrucciones:
            titulo = f"Audio {p}%"
            tab = ttk.Frame(self.notebook)
            self.notebook.add(tab, text=titulo)

            controles = ttk.Frame(tab)
            controles.pack(side="top", fill="x", padx=10, pady=5)
            ttk.Button(controles, text="Reproducir original",
                       command=lambda s=senal: self._play_audio(s, fs)).pack(side="left", padx=5)
            ttk.Button(controles, text=f"Reproducir {p}%",
                       command=lambda r=rec: self._play_audio(r, fs)).pack(side="left", padx=5)
            ttk.Button(controles, text="Detener",
                       command=self._stop_audio).pack(side="left", padx=5)

            fig = plt.Figure(figsize=(10, 4))
            ax = fig.add_subplot(1, 1, 1)
            ax.plot(senal, label="Original")
            ax.plot(rec, label="Reconstruida")
            ax.legend()
            fig_canvas = FigureCanvasTkAgg(fig, master=tab)
            fig_canvas.draw()
            fig_canvas.get_tk_widget().pack(side="top", fill="both", expand=True)

    def _play_audio(self, data, fs):
        if self._sd is None:
            messagebox.showerror(
                "Error",
                "No se encontró el módulo 'sounddevice'. Instale con:\n\npip install sounddevice",
            )
            return
        try:
            self._sd.stop()
            self._sd.play(data, fs)
        except Exception as exc:
            messagebox.showerror("Error", f"No se pudo reproducir el audio: {exc}")

    def _stop_audio(self):
        if self._sd is not None:
            try:
                self._sd.stop()
            except Exception:
                pass



def iniciar_aplicacion():
    app = AplicacionDCT()
    app.mainloop()
