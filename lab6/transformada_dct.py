# transformada_dct.py
# --------------------------------------------------------
# Implementación de la Transformada Discreta del Coseno (DCT-II)
# y su inversa (IDCT-II) usando SciPy con normalización ortonormal.
# Esta implementación cumple la teoría del documento de clase:
#   - DCT tipo 2
#   - Factores alfa_k equivalentes a norm="ortho"
# --------------------------------------------------------

import numpy as np
from scipy.fft import dct, idct

def dct_1d(senal):
    """
    Aplica la DCT tipo II (1D) a una señal real.

    Parámetros
    ----------
    senal : array_like
        Señal en el dominio del tiempo.

    Retorna
    -------
    np.ndarray
        Coeficientes DCT de la señal.
    """
    senal = np.asarray(senal, dtype=float)
    return dct(senal, type=2, norm="ortho")


def idct_1d(coeficientes):
    """
    Aplica la IDCT tipo II (1D) a un conjunto de coeficientes DCT.

    Parámetros
    ----------
    coeficientes : array_like
        Coeficientes DCT de la señal.

    Retorna
    -------
    np.ndarray
        Señal reconstruida en el dominio del tiempo.
    """
    coeficientes = np.asarray(coeficientes, dtype=float)
    return idct(coeficientes, type=2, norm="ortho")
