import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox
import threading

from diseno_bilineal import disenar_butterworth_pasabanda_orden2_bilineal
from biquad import FiltroBiquadOrden2
from dft_manual import calcular_dft_real
from graficos_ttk import trazar_espectros_dobles
from audio_io import grabar_voz, reproducir_audio, guardar_wav, pyaudio


class AplicacionFiltro(ttk.Window):
    def __init__(self):
        super().__init__(themename="darkly")
        self.title("Filtro Butterworth Pasabanda - Orden 2 (Bilineal)")
        self.geometry("1220x880")

        # Estilos base (fuentes y contraste)
        style = self.style  # ttk.Window expone una propiedad 'style' de solo lectura
        style.configure("TLabel", font=("Segoe UI", 10))
        style.configure("TButton", font=("Segoe UI", 10))
        # Título y subtítulo sin fondo blanco; alto contraste en tema oscuro
        style.configure("Title.TLabel", font=("Segoe UI", 14, "bold"), foreground="#e6edf3")
        style.configure("Subtitle.TLabel", font=("Segoe UI", 10), foreground="#9da7b3")

        # Variables principales
        self.frecuencia_muestreo_hz = ttk.StringVar(value="44100")
        self.frecuencia_corte_baja_hz = ttk.StringVar(value="2000")
        self.frecuencia_corte_alta_hz = ttk.StringVar(value="4000")
        self.duracion_grabacion_s = ttk.StringVar(value="6")
        self.texto_coeficientes = ttk.StringVar(value="Coeficientes: b0=?, b1=?, b2=?, a1=?, a2=?")
        self.texto_parametros = ttk.StringVar(value="Parametros: w1=?, w2=?, w0=?, BW=?")
        self.senal_original = []
        self.senal_filtrada = []
        self.biquad = None

        self._crear_gui()

    # ===================== Helpers seguros para hilos =====================
    def _set_estado_grabacion(self, texto, bootstyle):
        self.after(0, lambda: self.estado_grabacion.config(text=texto, bootstyle=bootstyle))

    def _dibujar_espectros_seguro(self, magnitudes_o, magnitudes_f):
        self.after(0, lambda: trazar_espectros_dobles(self.canvas_espectros, magnitudes_o, magnitudes_f))

    # ===================== Construccion GUI =====================
    def _crear_gui(self):
        root = ttk.Frame(self, padding=14)
        root.pack(fill="both", expand=True)

        # Header
        header = ttk.Frame(root)
        header.pack(fill="x", pady=(0, 8))
        ttk.Label(header, text="Filtro Butterworth Pasabanda (Orden 2)",
                  style="Title.TLabel").pack(side="left")
        ttk.Label(header, text="Diseno bilineal • Audio DSP",
                  style="Subtitle.TLabel").pack(side="left", padx=10)

        # Contenido principal: panel de control + canvas
        contenido = ttk.Frame(root)
        contenido.pack(fill="both", expand=True)

        # Panel lateral izquierdo
        panel = ttk.Labelframe(contenido, text="Parametros del Filtro", bootstyle="info", padding=12)
        panel.pack(side="left", fill="y", padx=(0, 12))

        self._fila(panel, "Frecuencia muestreo (Hz)", self.frecuencia_muestreo_hz).pack(anchor="w", pady=4)
        self._fila(panel, "fc1 (Hz)", self.frecuencia_corte_baja_hz).pack(anchor="w", pady=4)
        self._fila(panel, "fc2 (Hz)", self.frecuencia_corte_alta_hz).pack(anchor="w", pady=4)
        self._fila(panel, "Duracion (s)", self.duracion_grabacion_s).pack(anchor="w", pady=4)

        ttk.Separator(panel, bootstyle="dark").pack(fill="x", pady=8)

        ttk.Button(panel, text="Disenar Filtro", bootstyle="success-outline", command=self.on_disenar).pack(fill="x", pady=4)
        ttk.Button(panel, text="Grabar Voz", bootstyle="secondary-outline", command=self.on_grabar).pack(fill="x", pady=4)
        ttk.Button(panel, text="Filtrar Senal", bootstyle="primary-outline", command=self.on_filtrar).pack(fill="x", pady=4)
        ttk.Button(panel, text="Visualizar Espectros", bootstyle="warning-outline", command=self.on_visualizar_espectros).pack(fill="x", pady=6)

        ttk.Button(panel, text="Reproducir Original", bootstyle="info", command=self.on_reproducir_original).pack(fill="x", pady=(2, 2))
        ttk.Button(panel, text="Reproducir Filtrada", bootstyle="info", command=self.on_reproducir_filtrada).pack(fill="x", pady=(0, 6))

        self.estado_grabacion = ttk.Label(panel, text="Sin grabacion", bootstyle="secondary")
        self.estado_grabacion.pack(anchor="w", pady=6)

        ttk.Label(panel, textvariable=self.texto_coeficientes, wraplength=260, bootstyle="light").pack(anchor="w", pady=4)
        ttk.Label(panel, textvariable=self.texto_parametros, wraplength=260, bootstyle="light").pack(anchor="w", pady=4)

        # Panel derecho: espectros
        derecha = ttk.Labelframe(contenido, text="Visualizacion de Espectros", bootstyle="primary", padding=10)
        derecha.pack(side="left", fill="both", expand=True)

        self.canvas_espectros = tk.Canvas(
            derecha, bg="#1f2430", highlightthickness=2, highlightbackground="#343b46"
        )
        self.canvas_espectros.pack(fill="both", expand=True, padx=6, pady=6)

    def _fila(self, parent, texto, var):
        f = ttk.Frame(parent)
        ttk.Label(f, text=texto, bootstyle="secondary").pack(side="left", padx=3)
        ttk.Entry(f, textvariable=var, width=12, bootstyle="dark").pack(side="left", padx=8)
        return f

    # ===================== Lectura de parametros =====================
    def _leer_parametros(self):
        try:
            fs = int(self.frecuencia_muestreo_hz.get())
            fc1 = float(self.frecuencia_corte_baja_hz.get())
            fc2 = float(self.frecuencia_corte_alta_hz.get())
            dur = int(self.duracion_grabacion_s.get())
            if fc2 <= fc1 or fc2 > 5000:
                messagebox.showerror("Error", "Frecuencias invalidas (fc2>fc1 y <=5000 Hz).")
                return None
            return fs, fc1, fc2, dur
        except Exception:
            messagebox.showerror("Error", "Parametros invalidos.")
            return None

    # ===================== Funcionalidades =====================
    def on_disenar(self):
        params = self._leer_parametros()
        if not params:
            return
        fs, fc1, fc2, dur = params
        b0, b1, b2, a1, a2, w0, BW, w1, w2 = disenar_butterworth_pasabanda_orden2_bilineal(fc1, fc2, fs)
        self.biquad = FiltroBiquadOrden2(b0, b1, b2, a1, a2)
        self.texto_coeficientes.set(f"b0={b0:.3e}, b1={b1:.3e}, b2={b2:.3e}, a1={a1:.3e}, a2={a2:.3e}")
        self.texto_parametros.set(f"w0={w0:.2f}, BW={BW:.2f}, w1={w1:.2f}, w2={w2:.2f}")

    def on_grabar(self):
        params = self._leer_parametros()
        if not params:
            return
        fs, fc1, fc2, dur = params

        def tarea():
            self._set_estado_grabacion("Grabando...", "danger")
            try:
                datos = grabar_voz(dur, fs)
                self.senal_original = datos
                self._set_estado_grabacion("Audio grabado correctamente", "success")
            except Exception as e:
                self._set_estado_grabacion("Error en grabacion", "danger")
                self.after(0, lambda: messagebox.showerror("Error de audio", str(e)))

        threading.Thread(target=tarea, daemon=True).start()

    def on_filtrar(self):
        params = self._leer_parametros()
        if not params or not self.senal_original or not self.biquad:
            messagebox.showwarning("Advertencia", "Falta senal o filtro disenado.")
            return
        fs, fc1, fc2, dur = params
        self.senal_filtrada = self.biquad.filtrar_bloque(self.senal_original)
        self._set_estado_grabacion("Senal filtrada lista", "success")

    def on_visualizar_espectros(self):
        params = self._leer_parametros()
        if not params:
            return
        fs, _, _, _ = params
        if not self.senal_original:
            messagebox.showwarning("Advertencia", "Debe grabar una senal antes de visualizar.")
            return
        if not self.senal_filtrada:
            messagebox.showwarning("Advertencia", "Debe filtrar la senal antes de visualizar.")
            return

        self._set_estado_grabacion("Calculando espectros...", "secondary")

        def tarea_fft():
            try:
                esp_o = calcular_dft_real(self.senal_original, fs)
                esp_f = calcular_dft_real(self.senal_filtrada, fs)
                N = min(len(esp_o), len(esp_f))
                if N == 0:
                    self._set_estado_grabacion("Espectros vacios", "warning")
                    return
                mags_o = [m for _, m in esp_o[:N]]
                mags_f = [m for _, m in esp_f[:N]]
                self._dibujar_espectros_seguro(mags_o, mags_f)
                self._set_estado_grabacion("Espectros visualizados correctamente", "success")
            except Exception as e:
                self._set_estado_grabacion("Error al graficar", "danger")
                self.after(0, lambda: messagebox.showerror("Error", f"Ocurrio un problema al graficar:\n{e}"))

        threading.Thread(target=tarea_fft, daemon=True).start()

    def on_reproducir_original(self):
        params = self._leer_parametros()
        if not params or not self.senal_original:
            return
        fs, _, _, _ = params
        reproducir_audio(self.senal_original, fs)

    def on_reproducir_filtrada(self):
        params = self._leer_parametros()
        if not params or not self.senal_filtrada:
            return
        fs, _, _, _ = params
        reproducir_audio(self.senal_filtrada, fs)


if __name__ == "__main__":
    AplicacionFiltro().mainloop()
