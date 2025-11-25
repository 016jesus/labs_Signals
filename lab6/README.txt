# README.txt

Laboratorio 6 - Transformada Discreta del Coseno (DCT) - Proyecto con SciPy
=======================================================================

Descripción
-----------
Este proyecto implementa la Transformada Discreta del Coseno (DCT) utilizando
la librería optimizada SciPy (scipy.fftpack) con normalización ortogonal,
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
    Contiene la clase AplicacionDCT (ventana principal) y la lógica de la interfaz:
    selección de archivo, modo (imagen/audio), porcentajes, dibujar gráficos y
    manejar los controles de audio.

- procesador_imagen_dct.py y procesar_imagen.py
    Implementación optimizada de DCT 2D usando scipy.fftpack.dct con normalización
    ortogonal. Procesa imágenes en bloques de 8x8 píxeles.

- procesador_audio_dct.py y procesar_audio.py
    Implementación optimizada de DCT 1D usando scipy.fftpack para audio.
    Funciones para:
      * Leer archivos WAV con soundfile (conversión automática a mono).
      * Aplicar DCT 1D con normalización ortogonal.
      * Filtrar coeficientes por magnitud absoluta.
      * Reconstruir señal mediante IDCT.
      * Calcular MSE y generar archivo WAV reconstruido.

Dependencias
------------
Debe instalar las siguientes librerías (además de Python 3.x):

- numpy
- scipy
- matplotlib
- opencv-python
- soundfile
- sounddevice
- ttkbootstrap

Se pueden instalar con:

    pip install numpy scipy matplotlib opencv-python soundfile sounddevice ttkbootstrap

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
- La DCT utiliza la implementación optimizada de SciPy (scipy.fftpack.dct/idct)
  con normalización ortogonal, proporcionando procesamiento eficiente incluso
  para señales largas e imágenes grandes.

- El mapa de calor de coeficientes DCT y los valores de MSE ayudan a justificar
  el análisis de calidad de compresión y la eficiencia del método.

- La interfaz incluye herramientas de zoom y paneo (NavigationToolbar2Tk) para
  análisis detallado de las reconstrucciones.
