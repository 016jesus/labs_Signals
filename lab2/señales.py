from typing import Tuple
import numpy as np

def generar_u(n: np.ndarray) -> np.ndarray:
    return (n >= 0).astype(float)

def señal_entrada(a: float, b: float, N: int) -> Tuple[np.ndarray, np.ndarray]:
    """x(n) = a e^{bn} u(n)."""
    n = np.arange(N, dtype=float)
    x = a * np.exp(b * n) * generar_u(n)
    return n, x

def respuesta_impulso(a: float, b: float, c: float, d: float, k: float, N: int) -> Tuple[np.ndarray, np.ndarray]:
    n = np.arange(N, dtype=float)
    h = np.zeros(N, dtype=float)

    A = np.exp(d + k)
    B = np.exp(d - k)
    r0 = np.exp(b)

    h[0] = c / a
    if N > 1:
        n1 = np.arange(1, N, dtype=float)
        term_A = (A - r0) * np.exp((d + k) * (n1 - 1))
        term_B = (B - r0) * np.exp((d - k) * (n1 - 1))
        h[1:] = (c / (2 * a)) * (term_A + term_B)

    return n, h

def salida_por_convolucion(x: np.ndarray, h: np.ndarray, N: int) -> np.ndarray:
    return np.convolve(x, h)[:N]

def salida_teorica(c: float, d: float, k: float, N: int) -> Tuple[np.ndarray, np.ndarray]:
    n = np.arange(N, dtype=float)
    y = c * np.exp(d * n) * np.cosh(k * n) * generar_u(n)
    return n, y
