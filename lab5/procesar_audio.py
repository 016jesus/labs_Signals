import numpy as np
import soundfile as sf
import matplotlib.pyplot as plt
from dct_manual import transformada_dct, transformada_idct
import os


def comprimir_senal_audio(ruta_audio, porcentaje_retenido):
    """Aplica DCT manual a una señal de voz, conserva coeficientes y reconstruye."""
    senal, fs = sf.read(ruta_audio)
    senal = senal / np.max(np.abs(senal))  # Normalización

    # Aplicar DCT
    coeficientes = transformada_dct(senal)

    total = len(coeficientes)
    cantidad_retenida = int((porcentaje_retenido / 100) * total)
    indices_ordenados = np.argsort(np.abs(coeficientes))[::-1]

    coef_filtrados = np.zeros_like(coeficientes)
    coef_filtrados[indices_ordenados[:cantidad_retenida]] = coeficientes[indices_ordenados[:cantidad_retenida]]

    # Reconstrucción
    senal_rec = transformada_idct(coef_filtrados)

    # Guardar y mostrar resultados
    sf.write("resultados/voz_reconstruida.wav", senal_rec, fs)
    mse = np.mean((senal - senal_rec) ** 2)

    plt.figure(figsize=(10, 4))
    plt.plot(senal, label="Original")
    plt.plot(senal_rec, label="Reconstruida", alpha=0.7)
    plt.title(f"Comparación de señal de voz (Compresión {porcentaje_retenido}%)")
    plt.legend()
    plt.show()

    print(f"Error cuadrático medio: {mse:.6f}")
