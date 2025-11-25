# procesar_imagen.py

import os
import numpy as np
import cv2
import matplotlib.pyplot as plt
from scipy.fftpack import dct, idct


def aplicar_dct_por_bloques(imagen, tamano_bloque=8):
    alto, ancho = imagen.shape
    dct_total = np.zeros_like(imagen, dtype=float)

    for i in range(0, alto, tamano_bloque):
        for j in range(0, ancho, tamano_bloque):
            bloque = imagen[i:i+tamano_bloque, j:j+tamano_bloque]
            if bloque.shape != (tamano_bloque, tamano_bloque):
                continue

            # DCT 2D separable con scipy (filas luego columnas)
            dct_bloque = dct(dct(bloque.T, norm='ortho').T, norm='ortho')

            dct_total[i:i+tamano_bloque, j:j+tamano_bloque] = dct_bloque

    return dct_total


def aplicar_idct_por_bloques(imagen_dct, tamano_bloque=8):
    alto, ancho = imagen_dct.shape
    reconstruida = np.zeros_like(imagen_dct, dtype=float)

    for i in range(0, alto, tamano_bloque):
        for j in range(0, ancho, tamano_bloque):
            bloque = imagen_dct[i:i+tamano_bloque, j:j+tamano_bloque]
            if bloque.shape != (tamano_bloque, tamano_bloque):
                continue

            # IDCT 2D separable con scipy (columnas luego filas)
            idct_bloque = idct(idct(bloque.T, norm='ortho').T, norm='ortho')

            reconstruida[i:i+tamano_bloque, j:j+tamano_bloque] = idct_bloque

    return np.clip(reconstruida, 0, 255).astype(np.uint8)


def _leer_imagen_grises(ruta_imagen: str):
    if not os.path.exists(ruta_imagen):
        return None
    try:
        datos = np.fromfile(ruta_imagen, dtype=np.uint8)
        if datos.size > 0:
            img = cv2.imdecode(datos, cv2.IMREAD_GRAYSCALE)
            if img is not None:
                return img
    except Exception:
        pass
    return cv2.imread(ruta_imagen, cv2.IMREAD_GRAYSCALE)


def comprimir_imagen(ruta_imagen, porcentaje_retenido):
    imagen = _leer_imagen_grises(ruta_imagen)
    if imagen is None:
        raise FileNotFoundError(f'No se pudo leer la imagen: {ruta_imagen}')

    tamano_bloque = 8
    alto, ancho = imagen.shape

    pad_h = (tamano_bloque - (alto % tamano_bloque)) % tamano_bloque
    pad_w = (tamano_bloque - (ancho % tamano_bloque)) % tamano_bloque

    if pad_h or pad_w:
        imagen_padded = np.pad(imagen, ((0, pad_h), (0, pad_w)), mode='edge')
    else:
        imagen_padded = imagen

    dct_img = aplicar_dct_por_bloques(imagen_padded, tamano_bloque=tamano_bloque)

    total = dct_img.size
    cantidad_retenida = int((porcentaje_retenido / 100.0) * total)
    cantidad_retenida = max(1, min(total, cantidad_retenida))

    plano = dct_img.flatten()
    indices = np.argsort(np.abs(plano))[::-1]
    plano_filtrado = np.zeros_like(plano)
    plano_filtrado[indices[:cantidad_retenida]] = plano[indices[:cantidad_retenida]]
    dct_filtrada = plano_filtrado.reshape(dct_img.shape)

    reconstruida_padded = aplicar_idct_por_bloques(dct_filtrada, tamano_bloque=tamano_bloque)
    reconstruida = reconstruida_padded[:alto, :ancho]

    mse = float(np.mean((imagen.astype(np.float32) - reconstruida.astype(np.float32)) ** 2))

    os.makedirs('resultados', exist_ok=True)
    cv2.imwrite('resultados/imagen_reconstruida.png', reconstruida)

    # Grafico comparativo y mapa de calor de coeficientes
    plt.figure(figsize=(12, 4))
    plt.subplot(1, 3, 1)
    plt.imshow(imagen, cmap='gray')
    plt.title('Original')
    plt.axis('off')

    plt.subplot(1, 3, 2)
    plt.imshow(reconstruida, cmap='gray')
    plt.title(f'Reconstruida ({porcentaje_retenido:.1f}%)')
    plt.axis('off')

    plt.subplot(1, 3, 3)
    plt.imshow(np.log1p(np.abs(dct_img)), cmap='inferno')
    plt.title('Mapa |DCT| (log)')
    plt.axis('off')

    plt.suptitle(f'Compresión DCT con SciPy - MSE={mse:.4f}', fontsize=10)
    plt.tight_layout()
    plt.show()

    print(f'Error cuadrático medio (MSE): {mse:.6f}')
    return reconstruida, mse
