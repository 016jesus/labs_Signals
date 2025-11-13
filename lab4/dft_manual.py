"""
Módulo: dfr_manual.py
-------------------------------------
Cálculo del espectro (DFT real) usando librerías optimizadas (NumPy FFT)
en lugar del cálculo manual por bucles.
"""

import numpy as np
from math import sqrt


def calcular_dft_real(senal, frecuencia_muestreo_hz):
    """
    Calcula el espectro de magnitud de una señal real usando FFT (NumPy).
    Retorna una lista de tuplas (frecuencia_hz, magnitud_lineal).
    """
    if senal is None or len(senal) == 0:
        return []

    x = np.asarray(senal, dtype=np.float64)
    N = x.size

    # FFT real (eficiente)
    X = np.fft.rfft(x)
    magnitud = np.abs(X)

    # Vector de frecuencias correspondiente (Hz)
    freqs = np.fft.rfftfreq(N, d=1.0 / float(frecuencia_muestreo_hz))

    return list(zip(freqs.tolist(), magnitud.tolist()))


def respuesta_en_frecuencia_por_impulso(filtro_biquad, frecuencia_muestreo_hz, longitud=2048):
    """
    Calcula la respuesta en frecuencia del filtro aplicando un impulso
    y obteniendo su FFT real (optimizada).
    """
    if filtro_biquad is None:
        return []

    # Generar impulso unitario (delta[n])
    h = np.zeros(int(longitud))
    h[0] = 1.0

    # Filtrar el impulso con el biquad
    resp = np.array(filtro_biquad.filtrar_bloque(h.tolist()))

    # FFT del resultado
    X = np.fft.rfft(resp)
    magnitud = np.abs(X)
    freqs = np.fft.rfftfreq(len(resp), d=1.0 / float(frecuencia_muestreo_hz))

    return list(zip(freqs.tolist(), magnitud.tolist()))
