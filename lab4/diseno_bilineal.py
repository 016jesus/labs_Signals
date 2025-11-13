"""
Módulo: diseno_bilineal.py
-------------------------------------
Diseño matemático completo del filtro Butterworth pasabanda de orden 2
usando la Transformación Bilineal paso a paso, según el desarrollo teórico
del documento del curso.

Incluye el cálculo de las constantes analógicas a,b,c,d,e y los coeficientes
discretos A0,A2,A4,B0,B1,B2,B3,B4 conforme a la ecuación en diferencias:
    y[n] = (1/B0)*(A0*x[n] - A2*x[n-2] + A4*x[n-4]
                   - B1*y[n-1] - B2*y[n-2] - B3*y[n-3] - B4*y[n-4])
"""

from math import pi, tan, sqrt


# ========================= 1. Funciones base =========================

def calcular_warp(fc_hz, fs_hz):
    """Frecuencia analógica prewarp para compensar distorsión de Tustin."""
    return 2.0 * fs_hz * tan(pi * (fc_hz / fs_hz))


def obtener_parametros_analogicos(fc1_hz, fc2_hz, fs_hz):
    """Calcula ω0 (rad/s) y ancho de banda BW analógico (rad/s)."""
    Omega1 = calcular_warp(fc1_hz, fs_hz)
    Omega2 = calcular_warp(fc2_hz, fs_hz)
    omega0 = sqrt(Omega1 * Omega2)     # Frecuencia central analógica
    BW = Omega2 - Omega1               # Ancho de banda analógico
    return omega0, BW


# ========================= 2. Constantes a,b,c,d,e =========================

def constantes_ABCDE(omega0, BW):
    """
    Cálculo de las constantes analógicas según el modelo teórico del filtro:
        a = BW^2
        b = sqrt(2)*BW
        c = 2*omega0^2 + BW^2
        d = sqrt(2)*BW*omega0^2
        e = omega0^4
    """
    a = BW**2
    b = sqrt(2) * BW
    c = 2 * (omega0**2) + BW**2
    d = sqrt(2) * BW * (omega0**2)
    e = omega0**4
    return a, b, c, d, e


# ========================= 3. Coeficientes discretos =========================

def coeficientes_diferencias(a, b, c, d, e, fs_hz):
    """
    Genera los coeficientes A0,A2,A4,B0,B1,B2,B3,B4 de la ecuación discreta
    luego de aplicar la transformada bilineal con T = 1/fs.
    """
    T = 1.0 / fs_hz

    A0 = 4 * a * (T**2)
    A2 = 8 * a * (T**2)
    A4 = 4 * a * (T**2)

    B0 = 16 + 8*b*T + 4*c*(T**2) + 2*d*(T**3) + e*(T**4)
    B1 = -64 - 16*b*T + 4*d*(T**3) + 4*e*(T**4)
    B2 = 96 - 8*c*(T**2) + 6*e*(T**4)
    B3 = -64 + 16*b*T - 4*d*(T**3) + 4*e*(T**4)
    B4 = 16 - 8*b*T + 4*c*(T**2) - 2*d*(T**3) + e*(T**4)

    return A0, A2, A4, B0, B1, B2, B3, B4


# ========================= 4. Función general de diseño =========================

def disenar_butterworth_pasabanda_bilineal_teorico(fc1_hz, fc2_hz, fs_hz):
    """
    Diseña un filtro Butterworth pasabanda de 2° orden con bilineal completa
    según las ecuaciones del desarrollo teórico del laboratorio.

    Retorna:
      A0,A2,A4,B0,B1,B2,B3,B4 : coeficientes de la ecuación en diferencias
      a,b,c,d,e,omega0,BW,T   : parámetros analógicos y de discretización
    """
    omega0, BW = obtener_parametros_analogicos(fc1_hz, fc2_hz, fs_hz)
    a, b, c, d, e = constantes_ABCDE(omega0, BW)
    A0, A2, A4, B0, B1, B2, B3, B4 = coeficientes_diferencias(a, b, c, d, e, fs_hz)
    T = 1.0 / fs_hz
    return A0, A2, A4, B0, B1, B2, B3, B4, a, b, c, d, e, omega0, BW, T


# ========================= 5. Prueba de validación =========================

if __name__ == "__main__":
    fs = 44100
    fc1 = 2000
    fc2 = 4000

    (A0, A2, A4, B0, B1, B2, B3, B4, a, b, c, d, e, omega0, BW, T) = disenar_butterworth_pasabanda_bilineal_teorico(fc1, fc2, fs)

    print("\n=== Parámetros analógicos ===")
    print(f"a={a:.3e}, b={b:.3e}, c={c:.3e}, d={d:.3e}, e={e:.3e}")
    print(f"ω0={omega0:.3f} rad/s, BW={BW:.3f} rad/s, T={T:.3e}")

    print("\n=== Coeficientes discretos ===")
    print(f"A0={A0:.6e}, A2={A2:.6e}, A4={A4:.6e}")
    print(f"B0={B0:.6e}, B1={B1:.6e}, B2={B2:.6e}, B3={B3:.6e}, B4={B4:.6e}")

    print("\nEcuación de diferencias final:")
    print("y[n] = (1/B0)*(A0*x[n] - A2*x[n-2] + A4*x[n-4] - B1*y[n-1] - B2*y[n-2] - B3*y[n-3] - B4*y[n-4])")
