# dct_manual.py

import math
import numpy as np

_FAST_THRESHOLD = 64  # para bloques pequenos (ej. 8x8) mantenemos la version clasica


def _dct_manual(senal):
    senal = list(senal)
    N = len(senal)
    resultado = [0.0] * N
    for k in range(N):
        factor = math.sqrt(1.0 / N) if k == 0 else math.sqrt(2.0 / N)
        suma = 0.0
        for n in range(N):
            angulo = math.pi * (n + 0.5) * k / N
            suma += senal[n] * math.cos(angulo)
        resultado[k] = factor * suma
    return resultado


def _idct_manual(coeficientes):
    coeficientes = list(coeficientes)
    N = len(coeficientes)
    resultado = [0.0] * N
    for n in range(N):
        suma = 0.0
        for k in range(N):
            factor = math.sqrt(1.0 / N) if k == 0 else math.sqrt(2.0 / N)
            angulo = math.pi * (n + 0.5) * k / N
            suma += factor * coeficientes[k] * math.cos(angulo)
        resultado[n] = suma
    return resultado


def _dct_fft(senal):
    x = np.asarray(senal, dtype=float).ravel()
    N = x.size
    if N == 0:
        return np.array([], dtype=float)

    extendida = np.empty(2 * N, dtype=float)
    extendida[:N] = x
    extendida[N:] = x[::-1]

    espectro = np.fft.fft(extendida)
    factores = np.exp(-1j * np.pi * np.arange(N) / (2 * N))
    resultado = np.real(espectro[:N] * factores)
    resultado *= 0.5
    if N > 0:
        resultado[0] *= np.sqrt(1.0 / N)
    if N > 1:
        resultado[1:] *= np.sqrt(2.0 / N)
    return resultado


def _idct_fft(coeficientes):
    c = np.asarray(coeficientes, dtype=float).ravel()
    N = c.size
    if N == 0:
        return np.array([], dtype=float)

    raw = c.copy()
    raw[0] *= 2.0 * np.sqrt(N)
    if N > 1:
        raw[1:] *= np.sqrt(2.0 * N)

    factores = np.exp(1j * np.pi * np.arange(N) / (2 * N))
    espectro = raw * factores

    extendida = np.empty(2 * N, dtype=complex)
    extendida[:N] = espectro
    extendida[N] = 0.0
    if N > 1:
        extendida[N + 1 :] = np.conjugate(espectro[1:][::-1])
    else:
        extendida[N + 1 :] = 0.0

    senal = np.fft.ifft(extendida).real[:N]
    return senal


def transformada_dct(senal):
    senal = list(senal)
    if len(senal) <= _FAST_THRESHOLD:
        return _dct_manual(senal)
    return _dct_fft(senal).tolist()


def transformada_idct(coeficientes):
    coeficientes = list(coeficientes)
    if len(coeficientes) <= _FAST_THRESHOLD:
        return _idct_manual(coeficientes)
    return _idct_fft(coeficientes).tolist()
