from math import pi, cos, sin, sqrt

try:
    import numpy as np  # Usar FFT acelerada en C cuando esté disponible
except Exception:  # pragma: no cover
    np = None


def _calcular_dft_real_lento(senal, fs):
    N = len(senal)
    res = []
    if N <= 0:
        return res
    for k in range(N // 2 + 1):
        r = 0.0
        im = 0.0
        for n in range(N):
            ang = 2.0 * pi * k * n / N
            r += senal[n] * cos(ang)
            im -= senal[n] * sin(ang)
        mag = sqrt(r * r + im * im)
        f = (fs * k) / N
        res.append((f, mag))
    return res


def calcular_dft_real(senal, frecuencia_muestreo_hz):
    """
    Devuelve la magnitud del espectro de la señal real usando rFFT si hay NumPy.
    Retorna una lista de pares (frecuencia_hz, magnitud_lineal).
    """
    if not senal:
        return []

    if np is None:
        # Fallback seguro (lento). Para evitar bloqueos, limitar tamaño.
        max_N = min(len(senal), 4096)
        return _calcular_dft_real_lento(senal[:max_N], frecuencia_muestreo_hz)

    x = np.asarray(senal, dtype=np.float64)
    N = x.size
    # FFT real (N/2+1 bins). Incluye DC y Nyquist.
    X = np.fft.rfft(x)
    mag = np.abs(X)
    freqs = np.fft.rfftfreq(N, d=1.0 / float(frecuencia_muestreo_hz))
    # Convertir a lista de tuplas para compatibilidad
    return list(zip(freqs.tolist(), mag.tolist()))


def respuesta_en_frecuencia_por_impulso(filtro_biquad, frecuencia_muestreo_hz, longitud=2048):
    h = [0.0] * int(longitud)
    h[0] = 1.0
    bq = filtro_biquad.clonar_reseteado()
    resp = bq.filtrar_bloque(h)
    return calcular_dft_real(resp, frecuencia_muestreo_hz)
