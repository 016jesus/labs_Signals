# procesar_audio.py

import os
import numpy as np
import soundfile as sf
import matplotlib.pyplot as plt

from dct_manual import transformada_dct, transformada_idct


def comprimir_senal_audio(ruta_audio, porcentaje_retenido):
    senal, fs = sf.read(ruta_audio)

    # Convertir a mono si es estéreo
    if hasattr(senal, 'ndim') and senal.ndim > 1:
        senal = senal.mean(axis=1)

    # Normalización segura
    max_abs = float(np.max(np.abs(senal)))
    if max_abs > 0:
        senal_norm = senal / max_abs
    else:
        senal_norm = senal

    # Aplicar DCT manual (convertimos a lista)
    coeficientes = transformada_dct(senal_norm.tolist())
    coeficientes = np.array(coeficientes, dtype=float)

    total = len(coeficientes)
    cantidad_retenida = int((porcentaje_retenido / 100.0) * total)
    cantidad_retenida = max(1, min(total, cantidad_retenida))

    indices_ordenados = np.argsort(np.abs(coeficientes))[::-1]
    coef_filtrados = np.zeros_like(coeficientes)
    coef_filtrados[indices_ordenados[:cantidad_retenida]] = coeficientes[indices_ordenados[:cantidad_retenida]]

    # Reconstrucción con IDCT manual
    senal_rec = transformada_idct(coef_filtrados.tolist())
    senal_rec = np.array(senal_rec, dtype=float)

    # Des-normalizamos
    if max_abs > 0:
        senal_rec = senal_rec * max_abs

    os.makedirs('resultados', exist_ok=True)
    salida = 'resultados/voz_reconstruida.wav'
    sf.write(salida, senal_rec, fs)

    mse = float(np.mean((senal - senal_rec) ** 2))

    plt.figure(figsize=(10, 4))
    plt.plot(senal, label='Original')
    plt.plot(senal_rec, label='Reconstruida', alpha=0.7)
    plt.title(f'Comparación señal de voz (Compresión {porcentaje_retenido:.1f}%)')
    plt.legend()
    plt.tight_layout()
    plt.show()

    print(f'Archivo de salida: {salida}')
    print(f'Error cuadrático medio (MSE): {mse:.6f}')
    return senal_rec, fs, mse
