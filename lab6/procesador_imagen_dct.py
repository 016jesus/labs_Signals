import numpy as np
import cv2
from scipy.fftpack import dct, idct


def leer_imagen_grises(ruta):
    import numpy as np
    
    try:
        with open(ruta, "rb") as f:
            datos = f.read()
        np_arr = np.frombuffer(datos, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_GRAYSCALE)
        if img is None:
            return None
        return img.astype(float)
    except Exception as e:
        print("Error al leer imagen:", e)
        return None



def aplicar_dct_bloques(img, bloque=8):
    h, w = img.shape
    original_shape = img.shape

    pad_h = (bloque - (h % bloque)) % bloque
    pad_w = (bloque - (w % bloque)) % bloque
    img = np.pad(img, ((0, pad_h), (0, pad_w)), mode="edge")

    dct_total = np.zeros_like(img)

    for i in range(0, img.shape[0], bloque):
        for j in range(0, img.shape[1], bloque):
            b = img[i:i+bloque, j:j+bloque]
            d1 = dct(dct(b.T, norm='ortho').T, norm='ortho')
            dct_total[i:i+bloque, j:j+bloque] = d1

    return dct_total, original_shape


def aplicar_idct_bloques(dct_img, bloque=8, original_shape=None):
    h, w = dct_img.shape
    rec = np.zeros_like(dct_img)

    for i in range(0, h, bloque):
        for j in range(0, w, bloque):
            b = dct_img[i:i+bloque, j:j+bloque]
            id1 = idct(idct(b.T, norm='ortho').T, norm='ortho')
            rec[i:i+bloque, j:j+bloque] = id1

    rec = np.clip(rec, 0, 255).astype(np.uint8)

    if original_shape is not None:
        rec = rec[: original_shape[0], : original_shape[1]]

    return rec


def filtrar_coeficientes_pequenos_imagen(dct_img, porcentaje):
    plano = dct_img.flatten()
    total = len(plano)

    k = int((porcentaje / 100.0) * total)
    if k < 1:
        return dct_img.copy()

    idx = np.argsort(np.abs(plano))

    filtrada = plano.copy()
    filtrada[idx[:k]] = 0  # eliminar los k coeficientes más pequeños

    return filtrada.reshape(dct_img.shape)
