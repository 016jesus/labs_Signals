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
    Técnica de banco de filtros por FFT según el documento del laboratorio.
    *** VERSIÓN MEJORADA CON PREPROCESAMIENTO ROBUSTO ***
    
    Proceso:
    1. Pre-énfasis (realza altas frecuencias - mejor para consonantes)
    2. Eliminación DC
    3. Detección actividad voz (VAD) - elimina silencios
    4. Normalización de energía (independiente del volumen)
    5. Aplicar ventana a la señal
    6. Calcular FFT completa
    7. Dividir espectro en K subbandas por particionamiento directo de bins
    8. Calcular energía por subbanda: E = (1/N) * Σ|X(k)|²
    9. Normalización logarítmica y distribución relativa
    
    Retorna: (E[K], bands[Kx2] en Hz, freqs rFFT estándar para N)
    """
    
    # ========== PREPROCESAMIENTO ROBUSTO ==========
    # 1. Detección de actividad de voz (eliminar silencios)
    frame_len = int(0.01 * fs)  # 10 ms
    energy_frames = []
    for i in range(0, len(x) - frame_len, frame_len // 2):
        e = np.sqrt(np.mean(x[i:i+frame_len] ** 2))
        energy_frames.append(e)
    
    if len(energy_frames) > 0:
        energy_frames = np.array(energy_frames)
        max_e = np.max(energy_frames)
        if max_e > 0:
            threshold = max_e * (10 ** (-30 / 20))  # -30 dB
            voice_frames = np.where(energy_frames > threshold)[0]
            if len(voice_frames) > 0:
                start_idx = voice_frames[0] * (frame_len // 2)
                end_idx = min((voice_frames[-1] + 2) * (frame_len // 2), len(x))
                x = x[start_idx:end_idx]
    
    # 2. Eliminar componente DC
    x = x - np.mean(x)
    
    # 3. Normalizar energía RMS (independiente del volumen de grabación)
    rms_val = np.sqrt(np.mean(x ** 2))
    if rms_val > 1e-8:
        x = x / rms_val * 0.1  # RMS objetivo = 0.1
    
    # 4. Pre-énfasis: y[n] = x[n] - 0.97*x[n-1] (realza altas frecuencias)
    x = np.append(x[0], x[1:] - 0.97 * x[:-1])
    
    # ========== PREPARAR FRAME TAMAÑO N ==========
    if len(x) < N:
        xN = np.pad(x, (0, N - len(x)), mode='constant')
    elif len(x) > N:
        # Tomar centro (donde suele estar la voz)
        start = (len(x) - N) // 2
        xN = x[start:start + N]
    else:
        xN = x
    
    # ========== VENTANA ==========
    if window is None or window.lower() == "none" or window == "rect":
        w = np.ones(N)
    else:
        w = get_window(window, N, fftbins=True)

    # ========== FFT ==========
    xw = xN * w
    X = np.fft.rfft(xw, n=N)  # FFT real: devuelve N//2 + 1 bins
    freqs = np.fft.rfftfreq(N, d=1.0 / fs)
    
    # ========== PARTICIONAR EN K SUBBANDAS ==========
    num_bins = len(X)
    bands = partition_equal_bins(num_bins, K)
    
    # ========== CALCULAR ENERGÍAS POR SUBBANDA ==========
    Es = np.zeros(K, dtype=float)
    bands_hz = []
    
    for i, (start_bin, end_bin) in enumerate(bands):
        X_band = X[start_bin:end_bin]
        
        # Energía: E = (1/N) * Σ|X(k)|²
        E = np.sum(np.abs(X_band) ** 2) / N
        Es[i] = float(E)
        
        # Rangos de frecuencia en Hz
        f0 = freqs[start_bin]
        f1 = freqs[end_bin - 1] if end_bin > start_bin else freqs[start_bin]
        bands_hz.append((f0, f1))
    
    # ========== NORMALIZACIÓN LOGARÍTMICA ==========
    # Usar escala log para hacer comparaciones más robustas
    Es = np.log10(Es + 1e-10)
    
    # Normalizar para que sume 1 (distribución relativa de energía)
    E_sum = np.sum(Es)
    if E_sum != 0:
        Es = Es / E_sum

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
