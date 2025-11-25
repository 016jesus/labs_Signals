import os
import librosa
import soundfile as sf
import numpy as np

# Directorios de entrada y salida
input_directories = ["Arriba", "Abajo"]
output_directories = ["Arriba_procesado", "Abajo_procesado"]

# Método para detectar el inicio y fin de la palabra en la señal de audio
def detectar_inicio_fin(signal, threshold):
    inicio = None
    fin = None

    # Iterar sobre la señal
    for i, amp in enumerate(signal):
        if abs(amp) > threshold:
            if inicio is None:
                inicio = i
            fin = i
        elif inicio is not None:
            break

    return inicio, fin

# Método para procesar un archivo de audio
def procesar_audio(input_path, output_path, threshold=1):
    # Cargar la señal de audio y la frecuencia de muestreo
    signal, sr = librosa.load(input_path, sr=None)

    # Detectar el inicio y fin de la palabra de interés
    inicio, fin = detectar_inicio_fin(signal, threshold)

    # Cortar la señal para eliminar las partes no deseadas
    if inicio is not None and fin is not None:
        signal_recortada = signal[inicio:fin+1]
    else:
        signal_recortada = signal

    # Normalizar la longitud de la señal
    longitud_objetivo = 3 * 44100  # Duración deseada: 2 segundos
    if len(signal_recortada) < longitud_objetivo:
        # Calcular cuántos ceros agregar al principio y al final
        ceros_inicio = (longitud_objetivo - len(signal_recortada)) // 2
        ceros_final = longitud_objetivo - len(signal_recortada) - ceros_inicio
        # Rellenar con ceros
        signal_recortada = np.pad(signal_recortada, (ceros_inicio, ceros_final), mode='constant')
    elif len(signal_recortada) > longitud_objetivo:
        # Cortar la señal si es más larga de lo deseado
        signal_recortada = signal_recortada[:longitud_objetivo]

    # Guardar la señal procesada
    sf.write(output_path, signal_recortada, sr)

# Procesar archivos en los directorios de entrada
for input_dir, output_dir in zip(input_directories, output_directories):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    for file_name in os.listdir(input_dir):
        if file_name.endswith(".wav"):
            input_path = os.path.join(input_dir, file_name)
            output_path = os.path.join(output_dir, file_name)
            procesar_audio(input_path, output_path)
