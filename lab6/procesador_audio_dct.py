import numpy as np
import soundfile as sf
from scipy.fftpack import dct, idct


def cargar_audio(ruta):
    senal, fs = sf.read(ruta)
    if senal.ndim > 1:
        senal = senal.mean(axis=1)
    return senal.astype(float), fs


def dct_audio(senal):
    return dct(senal, norm='ortho')


def idct_audio(coef):
    return idct(coef, norm='ortho')


def filtrar_coeficientes_pequenos_audio(coef, porcentaje):
    total = len(coef)
    k = int((porcentaje / 100.0) * total)
    if k < 1:
        return coef.copy()

    idx = np.argsort(np.abs(coef))  # de menor a mayor
    filtrado = coef.copy()
    filtrado[idx[:k]] = 0

    return filtrado
