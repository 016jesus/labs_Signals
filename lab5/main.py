"""
GUI Laboratorio 5 - Reconocimiento de voz por segmentación temporal

MÉTODO DE RECONOCIMIENTO:
==========================
El sistema reconoce palabras dividiendo el audio en K segmentos temporales
y calculando la energía de cada pedazo:

1. ANÁLISIS DEL AUDIO:
   - Se toma el archivo de audio (señal de voz)
   - Se DIVIDE en K segmentos temporales (pedazos en el tiempo)
   - Para cada segmento: se calcula FFT y luego la ENERGÍA: E_k = Σ|X(f)|²
   - Resultado: vector de K energías [E₁, E₂, ..., E_K]
   
2. ENTRENAMIENTO:
   - Para cada palabra/comando, se graban M muestras
   - Se calcula el vector de energías [E₁, E₂, ..., E_K] de cada muestra
   - Se promedian para obtener el "patrón de energías" característico de cada palabra
   
3. RECONOCIMIENTO:
   - Se calcula el vector de energías del audio desconocido
   - Se compara con los patrones de cada palabra (distancia euclidiana)
   - La palabra con el patrón más similar (menor distancia) es la reconocida

Ejemplo con K=10 segmentos temporales:
- "segmentar" → energías típicas: [0.12, 0.28, 0.19, 0.17, 0.24, 0.10, 0.15, 0.08, 0.12, 0.05]
- "cifrar"    → energías típicas: [0.25, 0.15, 0.35, 0.10, 0.15, 0.20, 0.08, 0.12, 0.18, 0.07]
- "comprimir" → energías típicas: [0.08, 0.40, 0.18, 0.12, 0.22, 0.15, 0.10, 0.09, 0.14, 0.06]

Cada palabra tiene una "firma" de energías característica que permite distinguirlas.

Funciones principales:
- Entrenar: M grabaciones por cada comando, calcula energías por K segmentos
- Guardar/cargar modelo (JSON) con patrones de energía por comando
- Reconocer: desde micrófono o archivo WAV
- Visualizar: espectro y barras de energía por segmento
- Reconocimiento en tiempo real con detección de silencio
"""

import os
import json
import time
from typing import List, Tuple, Dict
import queue
import threading
from collections import deque

import numpy as np
import sounddevice as sd
import soundfile as sf
from scipy.signal import get_window

# Utils separadas
from audio_utils import ensure_dir, record_fixed_length, load_and_prepare_wav, enumerate_input_devices, parse_device_index
from dsp_utils import compute_subband_energies, compute_spectrum_mag, rms, dbfs_from_rms
from model_utils import train_from_folder, load_model, decide_label_by_min_dist

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


# ---------------------------
# Parámetros según enunciado del laboratorio
FS = 44100         # frecuencia de muestreo estándar (44.1 kHz)
N = 4096           # tamaño FFT por defecto (potencia de 2)
K = 3              # subbandas espectrales (SEGÚN ENUNCIADO: dividir en 3 subbandas)
M = 56            # grabaciones por defecto (SEGÚN ENUNCIADO: mínimo 100 por comando)
WINDOW = "hamming" # ventana por defecto
MODEL_PATH = "lab5_model.json"
RECORDINGS_DIR = "recordings"  # carpeta para guardar grabaciones
# ---------------------------


class Lab5GUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Lab 5 - Banco de filtros (3 comandos de voz)")
        self.model = None
        
        # Variables de configuración
        self.fs_var = tk.IntVar(value=FS)
        self.N_var = tk.IntVar(value=N)
        self.K_var = tk.IntVar(value=K)
        self.M_var = tk.IntVar(value=M)
        self.window_var = tk.StringVar(value=WINDOW)
        self.dir_var = tk.StringVar(value=RECORDINGS_DIR)
        
        # Etiquetas para 3 comandos
        self.labA_var = tk.StringVar(value="segmentar")
        self.labB_var = tk.StringVar(value="cifrar")
        self.labC_var = tk.StringVar(value="comprimir")
        
        self.status_var = tk.StringVar(value="Listo.")
        self.file_path_var = tk.StringVar(value="(ningún archivo)")

        # Dispositivos de entrada y medidor en tiempo real
        self.devices, self.hostapis = enumerate_input_devices()
        self.device_labels = [f"{i}: {d['name']}  [{self.hostapis.get(d['hostapi'], '?')}]" 
                             for i, d in enumerate(self.devices) if d.get('max_input_channels',0)>0]
        default_label = self.device_labels[0] if self.device_labels else "(predeterminado)"
        self.device_var = tk.StringVar(value=default_label)
        
        self.latest_rms = 0.0
        self.in_stream = None
        
        # Ring buffer y reconocimiento RT
        self.ring_seconds = 5.0
        self.ring_chunk = 0.1  # s
        self.ring_buf = deque(maxlen=int(self.ring_seconds / self.ring_chunk))
        self.ring_lock = threading.Lock()
        self._thr = threading
        self.recognizer_thread = None
        self.recognizer_stop = threading.Event()
        self.prev_rms = 0.0
        self.noise_rms = 0.0
        self.pred_label_var = tk.StringVar(value='-')
        self.pred_dists_var = tk.StringVar(value='-')
        self.confidence_var = tk.StringVar(value='-')
        self.validation_var = tk.StringVar(value='-')
        
        # Silencio: parámetros y estado
        self.silence_db_threshold = -50.0  # dBFS por debajo de este valor se considera silencio
        self.silence_min_time = 1.0        # segundos continuos de silencio para mostrar "Silencio"
        self.last_activity_time = time.time()
        
        # Tabla de sub-bandas
        self.subband_table = None
        self.subband_rows = []

        self._build_ui()
        self._start_input_meter()
        # Ticks UI
        self._tick_input_ui()

    def _build_ui(self):
        main = ttk.Frame(self.root, padding=10)
        main.pack(fill=tk.BOTH, expand=True)

        # ========== Parámetros ==========
        params = ttk.LabelFrame(main, text="Parámetros", padding=10)
        params.pack(fill=tk.X)
        
        ttk.Label(params, text="FS").grid(row=0, column=0, sticky='w', padx=4)
        ttk.Entry(params, textvariable=self.fs_var, width=8).grid(row=0, column=1, padx=4)
        
        ttk.Label(params, text="N").grid(row=0, column=2, sticky='w', padx=4)
        ttk.Entry(params, textvariable=self.N_var, width=8).grid(row=0, column=3, padx=4)
        
        ttk.Label(params, text="K").grid(row=0, column=4, sticky='w', padx=4)
        ttk.Entry(params, textvariable=self.K_var, width=5).grid(row=0, column=5, padx=4)
        
        ttk.Label(params, text="M").grid(row=0, column=6, sticky='w', padx=4)
        ttk.Entry(params, textvariable=self.M_var, width=5).grid(row=0, column=7, padx=4)
        
        ttk.Label(params, text="Ventana").grid(row=0, column=8, sticky='w', padx=4)
        ttk.Combobox(params, values=["hamming","hann","rect"], 
                    textvariable=self.window_var, state='readonly', width=10).grid(row=0, column=9, padx=4)

        ttk.Label(params, text="Grabaciones dir").grid(row=1, column=0, sticky='w', padx=4, pady=(6,0))
        ttk.Entry(params, textvariable=self.dir_var, width=40).grid(row=1, column=1, columnspan=7, padx=4, pady=(6,0), sticky='we')
        ttk.Button(params, text="Examinar", command=self._browse_dir).grid(row=1, column=8, padx=4, pady=(6,0))

        # ========== Entrada: micrófono y nivel ==========
        entry = ttk.LabelFrame(main, text="Entrada de micrófono", padding=10)
        entry.pack(fill=tk.X, pady=(8,0))
        
        ttk.Label(entry, text="Micrófono").grid(row=0, column=0, padx=4, sticky='w')
        self.dev_cb = ttk.Combobox(entry, values=self.device_labels, 
                                   textvariable=self.device_var, state='readonly', width=60)
        self.dev_cb.grid(row=0, column=1, padx=4, sticky='w')
        self.dev_cb.bind('<<ComboboxSelected>>', lambda e: self._restart_input_meter())
        
        ttk.Label(entry, text="Nivel").grid(row=1, column=0, padx=4, sticky='w')
        self.level_bar = ttk.Progressbar(entry, orient='horizontal', mode='determinate', length=280, maximum=1.0)
        self.level_bar.grid(row=1, column=1, padx=4, sticky='w')
        self.level_db_lbl = ttk.Label(entry, text="-∞ dBFS")
        self.level_db_lbl.grid(row=1, column=2, padx=4, sticky='w')

        # ========== Entrenamiento (3 comandos) ==========
        trainf = ttk.LabelFrame(main, text="Entrenamiento (3 comandos)", padding=10)
        trainf.pack(fill=tk.X, pady=(8,0))
        
        ttk.Label(trainf, text="Etiqueta A").grid(row=0, column=0, padx=4)
        ttk.Entry(trainf, textvariable=self.labA_var, width=10).grid(row=0, column=1, padx=4)
        
        ttk.Label(trainf, text="Etiqueta B").grid(row=0, column=2, padx=4)
        ttk.Entry(trainf, textvariable=self.labB_var, width=10).grid(row=0, column=3, padx=4)
        
        ttk.Label(trainf, text="Etiqueta C").grid(row=0, column=4, padx=4)
        ttk.Entry(trainf, textvariable=self.labC_var, width=10).grid(row=0, column=5, padx=4)
        
        ttk.Button(trainf, text=f"Grabar M por etiqueta", 
                  command=self._record_M_per_label).grid(row=1, column=0, columnspan=2, padx=6, pady=(6,0), sticky='we')
        ttk.Button(trainf, text="Entrenar desde carpetas", 
                  command=self._train_from_dirs).grid(row=1, column=2, columnspan=2, padx=6, pady=(6,0), sticky='we')
        ttk.Button(trainf, text="Guardar modelo", 
                  command=self._save_model_dialog).grid(row=1, column=4, padx=6, pady=(6,0), sticky='we')
        ttk.Button(trainf, text="Cargar modelo", 
                  command=self._load_model_dialog).grid(row=1, column=5, padx=6, pady=(6,0), sticky='we')

        # ========== Reconocimiento ==========
        recog = ttk.LabelFrame(main, text="Reconocimiento", padding=10)
        recog.pack(fill=tk.X, pady=(8,0))
        
        ttk.Button(recog, text="Reconocer 1 toma (N/fs)", 
                  command=self._recognize_mic).grid(row=0, column=0, padx=6)
        ttk.Button(recog, text="Seleccionar WAV", 
                  command=self._pick_file).grid(row=0, column=1, padx=6)
        ttk.Label(recog, textvariable=self.file_path_var).grid(row=0, column=2, padx=6, sticky='w')
        ttk.Button(recog, text="Predecir archivo", 
                  command=self._predict_file).grid(row=0, column=3, padx=6)
        
        ttk.Button(recog, text="Iniciar RT (5s buffer)", 
                  command=self._start_rt).grid(row=1, column=0, padx=6, pady=(6,0))
        ttk.Button(recog, text="Detener RT", 
                  command=self._stop_rt).grid(row=1, column=1, padx=6, pady=(6,0))
        ttk.Label(recog, text="Pred:").grid(row=1, column=2, padx=6, pady=(6,0), sticky='e')
        ttk.Label(recog, textvariable=self.pred_label_var, 
                 foreground='#b91c1c', font=(None, 11, 'bold')).grid(row=1, column=3, padx=6, pady=(6,0), sticky='w')
        
        ttk.Label(recog, text="Distancias:").grid(row=2, column=0, padx=6, pady=(2,0), sticky='e')
        ttk.Label(recog, textvariable=self.pred_dists_var).grid(row=2, column=1, columnspan=3, padx=6, pady=(2,0), sticky='w')
        
        # Confianza y validación
        ttk.Label(recog, text="Confianza:").grid(row=3, column=0, padx=6, pady=(2,0), sticky='e')
        self.confidence_label = ttk.Label(recog, textvariable=self.confidence_var, font=(None, 9, 'bold'))
        self.confidence_label.grid(row=3, column=1, columnspan=1, padx=6, pady=(2,0), sticky='w')
        
        ttk.Label(recog, text="Info:").grid(row=3, column=2, padx=6, pady=(2,0), sticky='e')
        self.validation_label = ttk.Label(recog, textvariable=self.validation_var, font=(None, 8))
        self.validation_label.grid(row=3, column=3, padx=6, pady=(2,0), sticky='w')
        
        # Nota informativa
        note_frame = ttk.Frame(recog)
        note_frame.grid(row=4, column=0, columnspan=4, padx=6, pady=(6,0), sticky='ew')
        note_text = "💡 Confianza = separación entre predicciones. ERROR REAL se calcula con validar.py"
        ttk.Label(note_frame, text=note_text, font=(None, 8), foreground='#6b7280').pack()

        # ========== Visualización ==========
        viz = ttk.LabelFrame(main, text="Visualización", padding=10)
        viz.pack(fill=tk.BOTH, expand=True, pady=(8,0))
        
        self.fig = Figure(figsize=(9,3))
        self.ax_spec = self.fig.add_subplot(121)
        self.ax_bar = self.fig.add_subplot(122)
        self.canvas = FigureCanvasTkAgg(self.fig, master=viz)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # ========== Tabla: energías por sub-banda ==========
        tblf = ttk.LabelFrame(main, text="Energías por sub-banda", padding=10)
        tblf.pack(fill=tk.X, pady=(8,0))
        
        self.subband_table = ttk.Treeview(tblf, columns=("banda","energia","porc"), show='headings', height=5)
        self.subband_table.heading("banda", text="Banda")
        self.subband_table.heading("energia", text="Energía")
        self.subband_table.heading("porc", text="%")
        self.subband_table.column("banda", width=80, anchor='center')
        self.subband_table.column("energia", width=140, anchor='e')
        self.subband_table.column("porc", width=80, anchor='e')
        self.subband_table.pack(fill=tk.X)
        self._ensure_subband_table_rows(int(self.K_var.get()))

        # ========== Status ==========
        status = ttk.Frame(main)
        status.pack(fill=tk.X, pady=(6,0))
        ttk.Label(status, textvariable=self.status_var).pack(side=tk.LEFT)

        self.fs_var.trace_add('write', lambda *args: self._restart_input_meter())

    def _browse_dir(self):
        d = filedialog.askdirectory(title='Seleccionar carpeta de grabaciones')
        if d:
            self.dir_var.set(d)

    def _log(self, msg: str):
        self.status_var.set(msg)
    
    def _calculate_confidence_and_validation(self, label: str, dists: dict) -> tuple:
        """
        Calcula métricas de confianza de la predicción.
        
        NOTA IMPORTANTE: 
        - La confianza aquí es una medida de qué tan separadas están las predicciones
        - NO es el error real del modelo
        - El ERROR REAL (< 5%) se calcula con validación usando el script validar.py
        
        La confianza indica:
        - Alta (>90%): La predicción tiene una distancia mucho menor que las demás
        - Media (70-90%): Hay cierta ambigüedad entre comandos
        - Baja (<70%): Las distancias son muy similares, predicción dudosa
        
        Retorna: (confidence_str, validation_str, confidence_percentage, is_confident, color)
        """
        if not dists or len(dists) < 2:
            return ("-", "-", 0.0, False, "#6b7280")
        
        # Obtener distancias ordenadas
        sorted_dists = sorted(dists.items(), key=lambda x: x[1])
        winner_label = sorted_dists[0][0]
        min_dist = sorted_dists[0][1]
        second_dist = sorted_dists[1][1]
        
        # Calcular separación relativa entre mejor y segunda opción
        # Si min_dist es mucho menor que second_dist → alta confianza
        if second_dist > 1e-6:
            separation_ratio = (second_dist - min_dist) / second_dist
            confidence_score = separation_ratio * 100
        else:
            confidence_score = 0.0
        
        # Penalizar si la distancia mínima es muy alta (patrón desconocido)
        # Distancias típicas buenas: 0.01-0.15
        # Distancias altas (>0.3): posible audio corrupto o comando desconocido
        if min_dist > 0.4:
            confidence_score *= 0.3  # Muy mala calidad
        elif min_dist > 0.3:
            confidence_score *= 0.5  # Mala calidad
        elif min_dist > 0.2:
            confidence_score *= 0.7  # Calidad regular
        
        confidence_score = min(100.0, max(0.0, confidence_score))
        
        # Clasificar confianza
        if confidence_score >= 90:
            confidence_level = "Alta"
            confidence_color = "#059669"  # Verde
        elif confidence_score >= 70:
            confidence_level = "Media"
            confidence_color = "#d97706"  # Amarillo/naranja
        else:
            confidence_level = "Baja"
            confidence_color = "#dc2626"  # Rojo
        
        # Formatear strings
        confidence_str = f"{confidence_score:.1f}% ({confidence_level})"
        
        # Mensaje informativo
        validation_str = f"Separación: {separation_ratio*100:.0f}% | Dist: {min_dist:.3f}"
        validation_color = confidence_color
        
        is_confident = confidence_score >= 70
        
        return (confidence_str, validation_str, confidence_score, is_confident, validation_color)
    
    def _update_confidence_display(self, label: str, dists: dict):
        """Actualiza la visualización de confianza"""
        confidence_str, info_str, conf_val, is_confident, color = \
            self._calculate_confidence_and_validation(label, dists)
        
        # Actualizar textos
        self.confidence_var.set(confidence_str)
        self.validation_var.set(info_str)
        
        # Actualizar colores
        self.confidence_label.config(foreground=color)
        self.validation_label.config(foreground=color)

    def _record_M_per_label(self):
        fs = int(self.fs_var.get())
        N = int(self.N_var.get())
        M = int(self.M_var.get())
        
        # 3 comandos
        labels = [
            self.labA_var.get().strip(), 
            self.labB_var.get().strip(),
            self.labC_var.get().strip()
        ]
        
        base = self.dir_var.get().strip()
        ensure_dir(base)
        dur = N / fs
        dev = parse_device_index(self.device_var.get())
        
        for lab in labels:
            sub = os.path.join(base, lab)
            ensure_dir(sub)
            for i in range(M):
                self._log(f"Grabando {lab} {i+1}/{M} ({dur:.2f}s)...")
                self.root.update()
                filename = os.path.join(sub, f"{lab}_{i+1}.wav")
                record_fixed_length(filename, dur, fs, device=dev)
                time.sleep(0.2)
        
        self._log("Grabaciones completadas.")

    def _train_from_dirs(self):
        fs = int(self.fs_var.get())
        N = int(self.N_var.get())
        K = int(self.K_var.get())
        M = int(self.M_var.get())
        base = self.dir_var.get().strip()
        
        # Mapeo para 3 comandos
        mapping = {
            self.labA_var.get().strip(): self.labA_var.get().strip(),
            self.labB_var.get().strip(): self.labB_var.get().strip(),
            self.labC_var.get().strip(): self.labC_var.get().strip()
        }
        
        try:
            self.model = train_from_folder(mapping, fs, N, K, M, self.window_var.get(), base, MODEL_PATH)
            self._log("Modelo entrenado con 3 comandos.")
        except Exception as e:
            messagebox.showerror("Error", f"Error al entrenar: {e}")
            self._log("Error al entrenar modelo.")

    def _save_model_dialog(self):
        if self.model is None:
            messagebox.showwarning('Sin modelo', 'Entrene o cargue un modelo primero')
            return
        path = filedialog.asksaveasfilename(title='Guardar modelo JSON', 
                                           defaultextension='.json', 
                                           filetypes=[('JSON','*.json')])
        if not path:
            return
        with open(path, 'w') as f:
            json.dump(self.model, f, indent=2)
        self._log(f"Modelo guardado en {path}")

    def _load_model_dialog(self):
        path = filedialog.askopenfilename(title='Cargar modelo JSON', 
                                         filetypes=[('JSON','*.json')])
        if not path:
            return
        try:
            self.model = load_model(path)
            self._log(f"Modelo cargado: {os.path.basename(path)} ({len(self.model.get('commands', {}))} comandos)")
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar modelo: {e}")

    def _recognize_mic(self):
        if self.model is None:
            messagebox.showwarning('Sin modelo', 'Cargue o entrene un modelo primero')
            return
        
        fs = self.model['fs']
        N = self.model['N']
        K = self.model['K']
        window = self.model['window']
        
        self._log(f"Capturando {N/fs:.2f}s desde mic...")
        dev = parse_device_index(self.device_var.get())
        
        data = sd.rec(int((N/fs) * fs), samplerate=fs, channels=1, dtype='float32', device=dev)
        sd.wait()
        x = data.flatten()
        x = x[:N] if len(x) >= N else np.pad(x, (0, N - len(x)))
        
        Es, bands, freqs = compute_subband_energies(x, fs, N, K, window)
        label, dists = decide_label_by_min_dist(Es, self.model, x_raw=data.flatten())
        
        self._log(f"Predicción: {label}  Distancias: {dists}")
        self._update_confidence_display(label, dists)
        self._update_plots(x, fs, N, window, freqs, Es, label)

    def _pick_file(self):
        p = filedialog.askopenfilename(title='Seleccionar WAV', filetypes=[('WAV','*.wav')])
        if p:
            self.file_path_var.set(p)

    def _predict_file(self):
        if self.model is None:
            messagebox.showwarning('Sin modelo', 'Cargue o entrene un modelo primero')
            return
        
        path = self.file_path_var.get()
        if not path or not os.path.isfile(path):
            self._pick_file()
            path = self.file_path_var.get()
            if not path or not os.path.isfile(path):
                return
        
        x, fsf = sf.read(path, dtype='float32')
        if x.ndim > 1:
            x = x.mean(axis=1)
        
        fs = self.model['fs']
        N = self.model['N']
        K = self.model['K']
        window = self.model['window']
        
        if fsf != fs:
            messagebox.showerror('Fs incompatible', 
                               f'El WAV tiene fs={fsf} y el modelo espera fs={fs}. Remuestrea/normaliza antes.')
            return
        
        x_orig = x.copy()  # Guardar señal original completa
        x = x[:N] if len(x) >= N else np.pad(x, (0, N - len(x)))
        
        Es, bands, freqs = compute_subband_energies(x, fs, N, K, window)
        label, dists = decide_label_by_min_dist(Es, self.model, x_raw=x_orig)
        
        self._log(f"Archivo: {os.path.basename(path)}  Predicción: {label}  Distancias: {dists}")
        self._update_confidence_display(label, dists)
        self._update_plots(x, fs, N, window, freqs, Es, label)

    def _update_plots(self, x: np.ndarray, fs: int, N: int, window: str, 
                     freqs: np.ndarray, Es: np.ndarray, label: str, mode: str | None = None):
        # Estilos y colores
        spec_color = "#2563eb"  # azul
        face = "#f9fafb"        # gris muy claro
        bar_palette = ["#10b981", "#3b82f6", "#f59e0b", "#ef4444", "#a855f7", "#14b8a6"]

        self.ax_spec.cla()
        self.ax_bar.cla()
        self.ax_spec.set_facecolor(face)
        self.ax_bar.set_facecolor(face)
        self.ax_spec.grid(True, alpha=0.25)

        if mode == "silence":
            # Placeholder de silencio
            self.ax_spec.text(0.5, 0.5, 'Silencio', ha='center', va='center', 
                            color="#6b7280", transform=self.ax_spec.transAxes)
            self.ax_spec.set_title('Espectro |X(k)|')
            self.ax_spec.set_xlabel('Frecuencia (rad/s)')
            self.ax_spec.set_ylabel('Magnitud |X(k)|')
            
            self.ax_bar.text(0.5, 0.5, 'Sin actividad', ha='center', va='center', 
                           color="#6b7280", transform=self.ax_bar.transAxes)
            self.ax_bar.set_title('Energías (pred: —)')
            
            self.fig.tight_layout()
            self.canvas.draw()
            
            # actualizar tabla con ceros si se pasó Es
            try:
                self._update_subband_table(Es)
            except Exception:
                pass
            return
        
 
        freqs_hz, mag = compute_spectrum_mag(x, fs, N, window)
        
       
        max_freq = 4000 
        idx_max = np.searchsorted(freqs_hz, max_freq)
        freqs_plot = freqs_hz[:idx_max]
        mag_plot = mag[:idx_max]
        
        self.ax_spec.plot(freqs_plot, mag_plot, color=spec_color, linewidth=1.2)
        self.ax_spec.set_title('Espectro |X(k)|')
        self.ax_spec.set_xlabel('Frecuencia (Hz)')
        self.ax_spec.set_ylabel('Magnitud |X(k)|')
        self.ax_spec.set_xlim(0, max_freq)
        self.ax_spec.grid(True, alpha=0.3)

        # Barras normalizadas para visual
        E_vis = Es / (Es.sum() + 1e-12)
        labels_b = [f"B{i}" for i in range(len(E_vis))]
        colors = [bar_palette[i % len(bar_palette)] for i in range(len(E_vis))]
        self.ax_bar.bar(labels_b, E_vis, color=colors)
        
        tit = f'Energías (pred: {label})' if label else 'Energías'
        self.ax_bar.set_title(tit)
        
        self.fig.tight_layout()
        self.canvas.draw()
        
        # Actualizar tabla
        self._update_subband_table(Es)

    def _ensure_subband_table_rows(self, k: int):
        # Reconstruye filas si el tamaño cambia
        current = len(self.subband_rows)
        if current != k:
            # limpiar
            for iid in self.subband_table.get_children():
                self.subband_table.delete(iid)
            self.subband_rows = []
            for i in range(k):
                iid = self.subband_table.insert('', 'end', values=(f"B{i}", f"0.0000", f"0.0"))
                self.subband_rows.append(iid)

    def _update_subband_table(self, Es: np.ndarray):
        if Es is None:
            return
        k = int(len(Es))
        self._ensure_subband_table_rows(k)
        total = float(np.sum(Es) + 1e-12)
        for i in range(k):
            e = float(Es[i])
            p = 100.0 * e / total if total > 0 else 0.0
            self.subband_table.item(self.subband_rows[i], values=(f"B{i}", f"{e:.6f}", f"{p:4.1f}"))

    def _start_input_meter(self):
        self._stop_input_meter()
        fs = int(self.fs_var.get())
        dev = parse_device_index(self.device_var.get())
        block = max(32, int(self.ring_chunk * fs))  # tamaño del chunk para ring (~100 ms)

        def cb(indata, frames, time_info, status):
            if status:
                return
            x = indata[:,0]
            # RMS
            r = rms(x)
            self.latest_rms = r
            # almacenar en buffer circular
            try:
                with (self.ring_lock or self._nullcontext()):
                    self.ring_buf.append(x.copy())
            except Exception:
                pass

        try:
            self.in_stream = sd.InputStream(samplerate=fs, channels=1, callback=cb, 
                                          blocksize=block, device=dev)
            self.in_stream.start()
        except Exception as e:
            self._log(f"No se pudo iniciar el medidor: {e}")
            self.in_stream = None

    def _stop_input_meter(self):
        try:
            if self.in_stream is not None:
                self.in_stream.stop()
                self.in_stream.close()
        except Exception:
            pass
        self.in_stream = None

    def _restart_input_meter(self):
        self._start_input_meter()

    def _tick_input_ui(self):
        r = float(self.latest_rms)
        db = dbfs_from_rms(r)
        self.level_db_lbl.config(text=f"{db:5.1f} dBFS")
        # Mapear -60..0 dB -> 0..1
        norm = np.clip((db + 60.0) / 60.0, 0.0, 1.0)
        self.level_bar['value'] = float(norm)
        self.root.after(50, self._tick_input_ui)

    def _start_rt(self):
        if self.model is None:
            messagebox.showwarning('Sin modelo', 'Cargue o entrene un modelo primero')
            return
        if self.recognizer_thread and self.recognizer_thread.is_alive():
            self._log('Reconocimiento RT ya en ejecución')
            return
        
        # comprobar fs del modelo
        fs = int(self.fs_var.get())
        if fs != int(self.model['fs']):
            messagebox.showerror('Fs incompatible', 
                               f'La GUI usa fs={fs} y el modelo espera fs={self.model["fs"]}. Ajusta FS.')
            return
        
        self.pred_label_var.set('-')
        self.pred_dists_var.set('-')
        self.confidence_var.set('-')
        self.validation_var.set('-')
        self.recognizer_stop.clear()
        self.prev_rms = 0.0
        self.noise_rms = 0.0
        self.recognizer_thread = self._thr.Thread(target=self._rt_worker, daemon=True)
        self.recognizer_thread.start()
        self._log('Reconocimiento RT iniciado')

    def _stop_rt(self):
        if self.recognizer_thread and self.recognizer_thread.is_alive():
            self.recognizer_stop.set()
            self.recognizer_thread.join(timeout=1.0)
        self._log('Reconocimiento RT detenido')

    def _assemble_last(self, num_samples: int) -> np.ndarray:
        with (self.ring_lock or self._nullcontext()):
            if len(self.ring_buf) == 0:
                return np.array([], dtype='float32')
            arr = np.concatenate(list(self.ring_buf)) if len(self.ring_buf) > 1 else self.ring_buf[0].copy()
        return arr[-num_samples:] if arr.size >= num_samples else arr

    def _rt_worker(self):
        fs = int(self.fs_var.get())
        N = int(self.N_var.get())
        K = int(self.K_var.get())
        window = self.window_var.get()
        frame_len = N  # muestras por frame
        
        # pequeña fase de estabilización para baseline (~0.5s)
        t0 = time.time()
        while (time.time() - t0) < 0.5 and not self.recognizer_stop.is_set():
            time.sleep(0.05)
        
        last_pred_time = 0.0
        
        while not self.recognizer_stop.is_set():
            buf = self._assemble_last(frame_len)
            if buf.size < frame_len:
                time.sleep(0.05)
                continue
            
            # energía (RMS) del frame actual
            r = rms(buf)
            db = dbfs_from_rms(r)
            
            # baseline con suavizado
            if self.noise_rms == 0.0:
                self.noise_rms = r
            self.noise_rms = 0.95*self.noise_rms + 0.05*r
            
            # criterio de cambio: subida significativa vs baseline o vs prev
            changed = (r > max(self.noise_rms*1.8, self.prev_rms*1.25))
            self.prev_rms = 0.9*self.prev_rms + 0.1*r if self.prev_rms>0 else r
            
            now = time.time()
            
            # Estado de silencio: dB muy bajos durante un tiempo
            is_silence = (db < self.silence_db_threshold)
            
            if is_silence:
                # Si estamos en silencio sostenido más allá del umbral, mostrar "Silencio".
                if (now - self.last_activity_time) > self.silence_min_time:
                    self.pred_label_var.set('silencio')
                    self.pred_dists_var.set('-')
                    self.confidence_var.set('-')
                    self.validation_var.set('-')
                    # Mostrar placeholder de silencio
                    self._update_plots(buf, fs, N, window, 
                                     np.linspace(0, fs/2, N//2+1), 
                                     np.zeros(K), '', mode="silence")
                else:
                    # Silencio reciente: deja el label en blanco
                    self.pred_label_var.set('')
                    self.pred_dists_var.set('')
                    self.confidence_var.set('')
                    self.validation_var.set('')
                time.sleep(0.05)
                continue
            else:
                # actividad detectada
                self.last_activity_time = now
            
            if changed and (now - last_pred_time) > 0.25:  # evitar exceso de triggers
                try:
                    Es, bands, freqs = compute_subband_energies(buf, fs, N, K, window)
                    label, dists = decide_label_by_min_dist(Es, self.model, x_raw=buf)
                    self.pred_label_var.set(label)
                    self.pred_dists_var.set(str({k:f"{v:.2f}" for k,v in dists.items()}))
                    self._update_confidence_display(label, dists)
                    self._log(f"RT: {label}  {dists}")
                    self._update_plots(buf, fs, N, window, freqs, Es, label)
                    last_pred_time = now
                except Exception as e:
                    self._log(f"Error RT: {e}")
            
            time.sleep(0.05)

    # nullcontext helper (for optional locks)
    class _nullcontext:
        def __enter__(self):
            return None
        def __exit__(self, exc_type, exc, tb):
            return False


if __name__ == "__main__":
    root = tk.Tk()
    app = Lab5GUI(root)
    root.mainloop()
