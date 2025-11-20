import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox
import threading

from diseno_bilineal import disenar_butterworth_pasabanda_bilineal_teorico
from biquad import FiltroButterworthPasabandaOrden4
from dft_manual import calcular_dft_real
from graficos_ttk import mostrar_espectros_en_frame, mostrar_2x2_en_frame
from audio_io import grabar_voz, reproducir_audio, guardar_wav, pyaudio


class AplicacionFiltro(ttk.Window):
    def __init__(self):
        super().__init__(themename="darkly")
        self.title("Filtro Butterworth Pasabanda - Orden 2 (Bilineal)")
        self.geometry("1220x880")

        # Estilos base (fuentes y contraste)
        style = self.style
        style.configure("TLabel", font=("Segoe UI", 10))
        style.configure("TButton", font=("Segoe UI", 10))
        style.configure("Title.TLabel", font=("Segoe UI", 14, "bold"), foreground="#e6edf3")
        style.configure("Subtitle.TLabel", font=("Segoe UI", 10), foreground="#9da7b3")

        # Variables principales
        self.frecuencia_muestreo_hz = ttk.StringVar(value="44100")
        self.frecuencia_corte_baja_hz = ttk.StringVar(value="2000")
        self.frecuencia_corte_alta_hz = ttk.StringVar(value="4000")
        self.duracion_grabacion_s = ttk.StringVar(value="6")
        self.texto_coeficientes = ttk.StringVar(
            value="Coeficientes: A0=?, A2=?, A4=?, B0=?, B1=?, B2=?, B3=?, B4=?"
        )
        self.texto_parametros = ttk.StringVar(value="Parametros: w1=?, w2=?, w0=?, BW=?")
        self.senal_original = []
        self.senal_filtrada = []
        self.filtro = None
        self.win_2x2 = None
        self.frame_espectros = None
        self.frame_2x2 = None
        self.tabs = None
        self.canvas_2x2 = None

        self._crear_gui()

    # ===================== Helpers =====================
    def _set_estado_grabacion(self, texto, bootstyle):
        self.after(0, lambda: self.estado_grabacion.config(text=texto, bootstyle=bootstyle))

    def _dibujar_espectros_seguro(self, espectro_o, espectro_f):
        self.after(0, lambda: mostrar_espectros_en_frame(self.frame_espectros, espectro_o, espectro_f))

    def _dibujar_2x2_seguro(self, fs, fc1, fc2):
        self.after(
            0,
            lambda: mostrar_2x2_en_frame(
                self.frame_2x2,
                self.senal_original,
                self.senal_filtrada,
                fs,
                fc1,
                fc2,
            ),
        )

    # ===================== GUI =====================
    def _crear_gui(self):
        root = ttk.Frame(self, padding=14)
        root.pack(fill="both", expand=True)

        header = ttk.Frame(root)
        header.pack(fill="x", pady=(0, 8))
        ttk.Label(header, text="Filtro Butterworth Pasabanda (Orden 2)",
                  style="Title.TLabel").pack(side="left")
        ttk.Label(header, text="Diseno bilineal • Audio DSP",
                  style="Subtitle.TLabel").pack(side="left", padx=10)

        contenido = ttk.Frame(root)
        contenido.pack(fill="both", expand=True)

        panel = ttk.Labelframe(contenido, text="Parametros del Filtro", bootstyle="info", padding=12)
        panel.pack(side="left", fill="y", padx=(0, 12))

        self._fila(panel, "Frecuencia muestreo (Hz)", self.frecuencia_muestreo_hz).pack(anchor="w", pady=4)
        self._fila(panel, "fc1 (Hz)", self.frecuencia_corte_baja_hz).pack(anchor="w", pady=4)
        self._fila(panel, "fc2 (Hz)", self.frecuencia_corte_alta_hz).pack(anchor="w", pady=4)
        self._fila(panel, "Duracion (s)", self.duracion_grabacion_s).pack(anchor="w", pady=4)

        ttk.Separator(panel, bootstyle="dark").pack(fill="x", pady=8)

        ttk.Button(panel, text="Disenar Filtro", bootstyle="success-outline", command=self.on_disenar).pack(fill="x", pady=4)
        ttk.Button(panel, text="Grabar Voz", bootstyle="secondary-outline", command=self.on_grabar).pack(fill="x", pady=4)
        ttk.Button(panel, text="Filtrar Señal", bootstyle="primary-outline", command=self.on_filtrar).pack(fill="x", pady=4)
        ttk.Button(panel, text="Visualizar Espectros", bootstyle="warning-outline", command=self.on_visualizar_espectros).pack(fill="x", pady=4)
        ttk.Button(panel, text="Analisis Espectral", bootstyle="warning", command=self.on_visualizar_2x2_nuevo).pack(fill="x", pady=6)

        ttk.Button(panel, text="Reproducir Original", bootstyle="info", command=self.on_reproducir_original).pack(fill="x", pady=(2, 2))
        ttk.Button(panel, text="Reproducir Filtrada", bootstyle="info", command=self.on_reproducir_filtrada).pack(fill="x", pady=(0, 6))

        self.estado_grabacion = ttk.Label(panel, text="Sin grabacion", bootstyle="secondary")
        self.estado_grabacion.pack(anchor="w", pady=6)

        ttk.Label(panel, textvariable=self.texto_coeficientes, wraplength=260, bootstyle="light").pack(anchor="w", pady=4)
        ttk.Label(panel, textvariable=self.texto_parametros, wraplength=260, bootstyle="light").pack(anchor="w", pady=4)

        # Tabs de visualización
        self.tabs = ttk.Notebook(contenido)
        self.tabs.pack(side="left", fill="both", expand=True)

        # Tab 1: Espectros
        tab_espectros = ttk.Frame(self.tabs)
        self.tabs.add(tab_espectros, text="Espectros")
        lf_espectros = ttk.Labelframe(tab_espectros, text="Visualizacion de Espectros", bootstyle="primary", padding=10)
        lf_espectros.pack(fill="both", expand=True)
        self.frame_espectros = ttk.Frame(lf_espectros)
        self.frame_espectros.pack(fill="both", expand=True, padx=6, pady=6)

        # Tab 2: 2x2
        tab_2x2 = ttk.Frame(self.tabs)
        self.tabs.add(tab_2x2, text="Analisis espectral")
        lf_2x2 = ttk.Labelframe(tab_2x2, text="Otras Graficas (2x2)", bootstyle="secondary", padding=10)
        lf_2x2.pack(fill="both", expand=True)
        self.frame_2x2 = ttk.Frame(lf_2x2)
        self.frame_2x2.pack(fill="both", expand=True, padx=6, pady=6)

    def _fila(self, parent, texto, var):
        f = ttk.Frame(parent)
        ttk.Label(f, text=texto, bootstyle="secondary").pack(side="left", padx=3)
        ttk.Entry(f, textvariable=var, width=12, bootstyle="dark").pack(side="left", padx=8)
        return f

    # ===================== Funciones principales =====================
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

    def on_disenar(self):
        params = self._leer_parametros()
        if not params:
            return
        fs, fc1, fc2, dur = params

        # === NUEVO DISENO TEORICO ===
        A0, A2, A4, B0, B1, B2, B3, B4, a, b, c, d, e, omega0, BW, T = disenar_butterworth_pasabanda_bilineal_teorico(fc1, fc2, fs)

        # === MAPEO ===
        w0 = omega0
        w1 = fc1
        w2 = fc2

        self.filtro = FiltroButterworthPasabandaOrden4(A0, A2, A4, B0, B1, B2, B3, B4)
        self.texto_coeficientes.set(
            f"A0={A0:.12e}, A2={A2:.12e}, A4={A4:.12e}, "
            f"B0={B0:.12e}, B1={B1:.12e}, B2={B2:.12e}, B3={B3:.12e}, B4={B4:.12e}"
        )
        self.texto_parametros.set(
            f"w0={w0:.12e}, BW={BW:.12e}, w1={w1:.12e}, w2={w2:.12e}"
        )

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
        if not params or not self.senal_original or not self.filtro:
            messagebox.showwarning("Advertencia", "Falta señal o filtro diseñado.")
            return
        self.senal_filtrada = self.filtro.filtrar_bloque(self.senal_original)
        self._set_estado_grabacion("Señal filtrada lista", "success")

    def on_visualizar_espectros(self):
        params = self._leer_parametros()
        if not params:
            return
        fs, _, _, _ = params
        if not self.senal_original or not self.senal_filtrada:
            messagebox.showwarning("Advertencia", "Debe grabar y filtrar la señal antes de visualizar.")
            return

        self._set_estado_grabacion("Calculando espectros...", "secondary")

        def tarea_fft():
            try:
                esp_o = calcular_dft_real(self.senal_original, fs)
                esp_f = calcular_dft_real(self.senal_filtrada, fs)
                self._dibujar_espectros_seguro(esp_o, esp_f)
                self._set_estado_grabacion("Espectros visualizados correctamente", "success")
            except Exception as e:
                self._set_estado_grabacion("Error al graficar", "danger")
                self.after(0, lambda: messagebox.showerror("Error", str(e)))

        threading.Thread(target=tarea_fft, daemon=True).start()

    def on_visualizar_2x2_nuevo(self):
        params = self._leer_parametros()
        if not params:
            return
        fs, fc1, fc2, _ = params
        if not self.senal_original or not self.senal_filtrada:
            messagebox.showwarning("Advertencia", "Debe grabar y filtrar la señal antes de visualizar.")
            return

        self._set_estado_grabacion("Calculando 2x2...", "secondary")

        def tarea_fft_2x2():
            try:
                self._dibujar_2x2_seguro(fs, fc1, fc2)
                self._set_estado_grabacion("2x2 listo", "success")
                self.tabs.select(1)
            except Exception as e:
                self._set_estado_grabacion("Error al graficar 2x2", "danger")
                self.after(0, lambda: messagebox.showerror("Error", str(e)))

        threading.Thread(target=tarea_fft_2x2, daemon=True).start()

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
