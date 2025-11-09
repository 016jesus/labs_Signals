import numpy as np

def transformada_dct(senal):
    """Implementación manual de la Transformada Discreta del Coseno tipo II"""
    longitud = len(senal)
    resultado = np.zeros(longitud)
    for k in range(longitud):
        factor = np.sqrt(1/longitud) if k == 0 else np.sqrt(2/longitud)
        suma = 0.0
        for n in range(longitud):
            suma += senal[n] * np.cos(np.pi * (n + 0.5) * k / longitud)
        resultado[k] = factor * suma
    return resultado


def transformada_idct(coeficientes):
    """Implementación manual de la Transformada Inversa Discreta del Coseno"""
    longitud = len(coeficientes)
    resultado = np.zeros(longitud)
    for n in range(longitud):
        suma = 0.0
        for k in range(longitud):
            factor = np.sqrt(1/longitud) if k == 0 else np.sqrt(2/longitud)
            suma += factor * coeficientes[k] * np.cos(np.pi * (n + 0.5) * k / longitud)
        resultado[n] = suma
    return resultado
