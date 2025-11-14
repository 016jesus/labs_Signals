
import math

def transformada_dct(senal):
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


def transformada_idct(coeficientes):
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
