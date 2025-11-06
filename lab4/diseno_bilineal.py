"""
Módulo: diseno_bilineal.py
-------------------------------------
Diseño de filtro Butterworth pasabanda de orden 2 usando
formulación de biquad equivalente a transformada bilineal
(Audio EQ Cookbook).
"""

from math import pi, sqrt, sin, cos


def disenar_butterworth_pasabanda_orden2_bilineal(fc1_hz, fc2_hz, fs_hz):
    """
    Diseña un filtro pasabanda de orden 2 (biquad) estilo Butterworth
    con bilineal (formulación tipo Audio EQ Cookbook) y a0=1.

    Parámetros
    ----------
    fc1_hz : float
        Frecuencia de corte inferior [Hz]
    fc2_hz : float
        Frecuencia de corte superior [Hz]
    fs_hz : float
        Frecuencia de muestreo [Hz]

    Retorna
    -------
    b0, b1, b2, a1, a2 : coeficientes del filtro digital (a0 = 1)
    w0, BW, w1, w2     : parámetros intermedios (frecuencias digitales)
    """

    # Frecuencias digitales (rad/muestra)
    w1 = 2 * pi * fc1_hz / fs_hz
    w2 = 2 * pi * fc2_hz / fs_hz

    # Frecuencia central y Q (ancho de banda)
    f0 = sqrt(fc1_hz * fc2_hz)
    w0 = 2 * pi * f0 / fs_hz
    BW = w2 - w1  # ancho de banda digital aproximado (rad/muestra)
    Q = f0 / (fc2_hz - fc1_hz)

    # Bandpass con pico ~ 0 dB en f0 (cookbook)
    alpha = sin(w0) / (2.0 * Q)
    b0 = alpha
    b1 = 0.0
    b2 = -alpha
    a0 = 1.0 + alpha
    a1 = -2.0 * cos(w0)
    a2 = 1.0 - alpha

    # Normalizar: a0 = 1
    b0 /= a0
    b1 /= a0
    b2 /= a0
    a1 /= a0
    a2 /= a0

    return b0, b1, b2, a1, a2, w0, BW, w1, w2


# ============================= Prueba rápida =============================
if __name__ == "__main__":
    fs = 44100
    fc1 = 2000
    fc2 = 4000

    b0, b1, b2, a1, a2, w0, BW, w1, w2 = disenar_butterworth_pasabanda_orden2_bilineal(fc1, fc2, fs)

    print("\nCoeficientes digitales obtenidos:")
    print(f"b0={b0:.6e}, b1={b1:.6e}, b2={b2:.6e}")
    print(f"a1={a1:.6e}, a2={a2:.6e}")
    print(f"\nParámetros: w0={w0:.3f}, BW={BW:.3f}, w1={w1:.3f}, w2={w2:.3f}")

