import os
import numpy as np
import soundfile as sf
import matplotlib.pyplot as plt
from dct_manual import transformada_dct, transformada_idct


def comprimir_senal_audio(ruta_audio, porcentaje_retenido):
    """Aplica DCT manual a una senal de voz, conserva coeficientes y reconstruye.

    Correcciones:
    - Convierte a mono si el WAV es estereo.
    - Normaliza de forma segura.
    - Asegura existencia de carpeta de salida.
    """
    senal, fs = sf.read(ruta_audio)
    if hasattr(senal, 'ndim') and senal.ndim > 1:
        senal = senal.mean(axis=1)

    max_abs = np.max(np.abs(senal))
    if max_abs > 0:
        senal = senal / max_abs

    coeficientes = transformada_dct(senal)

    total = len(coeficientes)
    cantidad_retenida = int((porcentaje_retenido / 100) * total)
    cantidad_retenida = max(1, min(total, cantidad_retenida))
    indices_ordenados = np.argsort(np.abs(coeficientes))[::-1]

    coef_filtrados = np.zeros_like(coeficientes)
    coef_filtrados[indices_ordenados[:cantidad_retenida]] = coeficientes[indices_ordenados[:cantidad_retenida]]

    senal_rec = transformada_idct(coef_filtrados)

    os.makedirs("resultados", exist_ok=True)
    sf.write("resultados/voz_reconstruida.wav", senal_rec, fs)
    mse = np.mean((senal - senal_rec) ** 2)

    plt.figure(figsize=(10, 4))
    plt.plot(senal, label="Original")
    plt.plot(senal_rec, label="Reconstruida", alpha=0.7)
    plt.title(f"Comparacion de senal de voz (Compresion {porcentaje_retenido}%)")
    plt.legend()
    plt.show()

    print(f"Error cuadratico medio: {mse:.6f}")

