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
    
    Proceso:
    1. Aplicar ventana a la señal
    2. Calcular FFT completa
    3. Dividir espectro en K subbandas por particionamiento directo de bins
    4. Calcular energía por subbanda: E = (1/N) * Σ|X(k)|²
    
    Retorna: (E[K], bands[Kx2] en Hz, freqs rFFT estándar para N)
    """
    # Ventana
    if window is None or window.lower() == "none" or window == "rect":
        w = np.ones(N)
    else:
        w = get_window(window, N, fftbins=True)

    # Preparar frame tamaño N
    if x.size < N:
        xN = np.pad(x, (0, N - x.size))
    else:
        xN = x[:N]

    # Aplicar ventana y calcular FFT completa
    xw = xN * w
    X = np.fft.rfft(xw, n=N)  # FFT real: devuelve N//2 + 1 bins
    
    # Vector de frecuencias
    freqs = np.fft.rfftfreq(N, d=1.0 / fs)
    
    # Particionar bins de FFT en K subbandas iguales
    num_bins = len(X)
    bands = partition_equal_bins(num_bins, K)
    
    # Calcular energía por subbanda: E = (1/N) * Σ|X(k)|²
    Es = np.zeros(K, dtype=float)
    bands_hz = []
    
    for i, (start_bin, end_bin) in enumerate(bands):
        # Extraer bins de esta subbanda
        X_band = X[start_bin:end_bin]
        
        # Energía: E = (1/N) * Σ|X(k)|²
        E = np.sum(np.abs(X_band) ** 2) / N
        Es[i] = float(E)
        
        # Rangos de frecuencia en Hz
        f0 = freqs[start_bin]
        f1 = freqs[end_bin - 1] if end_bin > start_bin else freqs[start_bin]
        bands_hz.append((f0, f1))

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
