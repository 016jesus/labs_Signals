import numpy as np
from math import sqrt


def calcular_dft_real(senal, frecuencia_muestreo_hz):
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
