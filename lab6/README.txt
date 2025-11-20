
Laboratorio 3 - Transformada Discreta del Coseno (DCT) - Proyecto Mejorado
=======================================================================

Descripción
-----------
Este proyecto implementa la Transformada Discreta del Coseno (DCT) de forma manual,
siguiendo la definición matemática (sin utilizar librerías de transformada como scipy),
y la aplica a:

- Compresión de imágenes en escala de grises mediante DCT 2D por bloques (estilo JPEG).
- Compresión de señales de audio (voz) con DCT 1D.

La interfaz gráfica está desarrollada con Tkinter + ttkbootstrap e incluye:

- Modo IMAGEN:
    * Visualización de la imagen original.
    * Mapa de calor de los coeficientes DCT (|DCT| en escala logarítmica).
    * Varias reconstrucciones con diferentes porcentajes de coeficientes retenidos.
    * Cálculo y visualización del MSE para cada porcentaje.

- Modo AUDIO:
    * Visualización de la señal original.
    * Reconstrucciones para diferentes porcentajes de coeficientes DCT.
    * Cálculo del MSE para cada reconstrucción.
    * Controles para reproducir el audio original y las versiones comprimidas.

Archivos principales
--------------------
- main.py
    Punto de entrada del programa. Lanza la interfaz gráfica.

- interfaz.py
    Contiene la clase App (ventana principal) y la lógica de la interfaz:
    selección de archivo, modo (imagen/audio), porcentajes, dibujar gráficos y
    manejar los controles de audio.

- dct_manual.py
    Implementación manual de la DCT-II y su inversa (IDCT) utilizando únicamente
    la librería estándar de Python (math) y bucles. No se utilizan librerías
    de transformada ni FFT.

- procesar_imagen.py
    Funciones para:
      * Leer imágenes a escala de grises.
      * Aplicar DCT 2D por bloques (8x8).
      * Aplicar IDCT 2D por bloques.
      * Comprimir y reconstruir imágenes reteniendo un porcentaje de coeficientes.

- procesar_audio.py
    Función para comprimir una señal de audio:
      * Lee un archivo WAV con soundfile.
      * Convierte a mono y normaliza.
      * Aplica DCT 1D manual.
      * Ordena coeficientes por magnitud, retiene un porcentaje y reconstruye.
      * Calcula MSE y genera un archivo WAV reconstruido.

Dependencias
------------
Debe instalar las siguientes librerías (además de Python 3.x):

- numpy
- matplotlib
- opencv-python
- soundfile
- simpleaudio
- ttkbootstrap

Se pueden instalar con:

    pip install numpy matplotlib opencv-python soundfile simpleaudio ttkbootstrap

Ejecución
---------
En una consola dentro de la carpeta del proyecto:

    python main.py

Luego:

1. Elija el modo (Imagen / Audio).
2. Seleccione el archivo:
    - Imagen: .png, .jpg, .jpeg, .bmp, .tif, .tiff
    - Audio: .wav
3. Ingrese los porcentajes de coeficientes DCT a retener (por ejemplo: 5,10,20,50).
4. Pulse "Procesar".

Notas
-----
- La DCT se implementa de manera matemática, por lo que el tiempo de procesamiento
  puede ser alto para señales muy largas o imágenes muy grandes. Esto es esperado
  en un contexto académico donde se debe evidenciar la implementación manual.

- El mapa de calor de coeficientes DCT y los valores de MSE ayudan a justificar
  el análisis de calidad de compresión y la eficiencia del método.
