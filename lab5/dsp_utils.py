"""
Funciones de DSP: subbandas por FFT, espectro, RMS y utilidades.
"""

from typing import Tuple, List
import numpy as np
from scipy.signal import get_window, butter, sosfilt


def partition_equal_bins(nbins: int, K: int) -> List[tuple]:
    """Particiona nbins en K grupos lo más iguales posible (por índice de bin)."""
    base = nbins // K
    remainder = nbins % K
    bands = []
    idx = 0
    for i in range(K):
        size = base + (1 if i < remainder else 0)
        bands.append((idx, idx + size))
        idx += size
    return bands


def _linear_subband_edges(fs: int, K: int) -> List[tuple]:
    """Devuelve K bandas lineales en Hz cubriendo [0, fs/2]."""
    fmax = fs / 2.0
    step = fmax / K
    edges = []
    for i in range(K):
        f0 = i * step
        f1 = fmax if i == (K - 1) else (i + 1) * step
        edges.append((f0, f1))
    return edges


def _design_sos_for_band(fs: int, f0: float, f1: float, order: int = 6):
    """Crea un filtro SOS (Butterworth) para la banda [f0,f1] Hz."""
    eps = 1e-6
    if f0 <= eps and f1 >= (fs / 2.0 - eps):
        # banda completa: paso-todo -> sin filtrar
        return None
    if f0 <= eps:
        # lowpass
        sos = butter(order, f1, btype='lowpass', output='sos', fs=fs)
    elif f1 >= (fs / 2.0 - eps):
        # highpass
        sos = butter(order, f0, btype='highpass', output='sos', fs=fs)
    else:
        sos = butter(order, [f0, f1], btype='bandpass', output='sos', fs=fs)
    return sos


def compute_subband_energies(x: np.ndarray, fs: int, N: int, K: int, window: str = "hamming") -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Calcula energías en K segmentos temporales de la señal x.
    """
    
    # ========== PASO 1: PREPROCESAMIENTO DE LA SEÑAL ==========
    
    # Eliminar componente DC (offset)
    x = x - np.mean(x)
    

    rms_val = np.sqrt(np.mean(x ** 2))
    if rms_val > 1e-8:
        x = x / rms_val
    
 
    x = np.append(x[0], x[1:] - 0.97 * x[:-1])
    
    # ========== PASO 2: PREPARAR SEÑAL DE TAMAÑO N ==========
    
    if len(x) < N:
        # Rellenar con ceros si es muy corto
        xN = np.pad(x, (0, N - len(x)), mode='constant')
    elif len(x) > N:
        # Tomar centro donde suele estar la voz
        start = (len(x) - N) // 2
        xN = x[start:start + N]
    else:
        xN = x
    
    # ========== PASO 3: DIVIDIR EN K SEGMENTOS TEMPORALES ==========
    
    segment_size = N // K
    Es = np.zeros(K, dtype=float)
    bands_hz = []  # Guardaremos rangos de frecuencia de cada segmento
    
    # Preparar ventana
    if window is None or window.lower() == "none" or window == "rect":
        w = np.ones(segment_size)
    else:
        w = get_window(window, segment_size, fftbins=True)
    
    # ========== PASO 4: CALCULAR ENERGÍA DE CADA SEGMENTO ==========
    
    for i in range(K):
        # Extraer segmento i del audio
        start_idx = i * segment_size
        end_idx = start_idx + segment_size if i < K - 1 else N
        segment = xN[start_idx:end_idx]
        
        # Ajustar tamaño del segmento si es necesario
        if len(segment) < segment_size:
            segment = np.pad(segment, (0, segment_size - len(segment)))
        elif len(segment) > segment_size:
            segment = segment[:segment_size]
    

        segment_windowed = segment * w    

        X_segment = np.fft.rfft(segment_windowed, n=segment_size)
    
        energy = np.sum(np.abs(X_segment) ** 2)
        Es[i] = float(energy)
        
        # Calcular rango de tiempo (y frecuencia dominante) de este segmento
        # Para compatibilidad con visualización
        freqs_segment = np.fft.rfftfreq(segment_size, d=1.0 / fs)
        f_min = freqs_segment[0]
        f_max = freqs_segment[-1]
        bands_hz.append((f_min, f_max))
    
    # ========== PASO 5: NORMALIZACIÓN PARA COMPARACIÓN ROBUSTA ==========
    
    # Evitar log(0) sumando epsilon pequeño
    Es = np.log10(Es + 1e-10)
    
    # Normalizar para que la suma sea 1 (distribución relativa de energía)
    # Esto hace que el reconocimiento sea independiente de la energía total
    E_sum = np.sum(Es)
    if E_sum != 0:
        Es = Es / E_sum
    
    # Para visualización, generamos frecuencias representativas
    freqs = np.fft.rfftfreq(segment_size, d=1.0 / fs)
    
    return Es, np.array(bands_hz), freqs


def compute_spectrum_db(x: np.ndarray, fs: int, N: int, window: str) -> tuple:
    """Devuelve (freqs, mag_db) del espectro de magnitud de x (rFFT) con ventana."""
    if window is None or window.lower() == "none" or window == "rect":
        w = np.ones(N)
    else:
        w = get_window(window, N, fftbins=True)
    xw = (x[:N] if x.size >= N else np.pad(x, (0, N - x.size))) * w
    X = np.abs(np.fft.rfft(xw, n=N))
    freqs = np.fft.rfftfreq(N, d=1.0 / fs)
    mag_db = 20.0 * np.log10(np.maximum(1e-12, X))
    return freqs, mag_db


def compute_spectrum_mag(x: np.ndarray, fs: int, N: int, window: str) -> tuple:
    """Devuelve (freqs_Hz, |X(k)|) del espectro de magnitud (rFFT) con ventana."""
    if window is None or window.lower() == "none" or window == "rect":
        w = np.ones(N)
    else:
        w = get_window(window, N, fftbins=True)
    xw = (x[:N] if x.size >= N else np.pad(x, (0, N - x.size))) * w
    X = np.abs(np.fft.rfft(xw, n=N))
    freqs = np.fft.rfftfreq(N, d=1.0 / fs)
    return freqs, X


def rms(x: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.square(x)) + 1e-12))


def dbfs_from_rms(r: float) -> float:
    return 20.0 * np.log10(max(1e-12, r))
