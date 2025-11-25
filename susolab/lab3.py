import numpy as np
import matplotlib.pyplot as plt
import sounddevice as sd
import os
import wave
from scipy import signal

# Parámetros para la grabación
duration = 2
sampling_rate = 44100

# Función para calcular la energía de una señal
def calcular_energia(signal):
    return np.sum(np.abs(signal) ** 2) / len(signal)

# Función para dividir una señal en dos sub-bandas y aplicar filtros pasa-bandas
def dividir_en_subbandas(input_signal, sampling_rate, f_cut_low, f_cut_high):
    # Calcular la frecuencia de corte en radianes/s
    w_low = 2 * np.pi * f_cut_low / sampling_rate
    w_high = 2 * np.pi * f_cut_high / sampling_rate
    
    # Diseñar filtro pasa-bandas
    b_bandpass, a_bandpass = signal.butter(4, [w_low, w_high], btype='bandpass')
    
    # Aplicar filtro pasa-bandas
    signal_bandpass = signal.filtfilt(b_bandpass, a_bandpass, input_signal)
    
    # Dividir la señal en dos sub-bandas
    mid = len(signal_bandpass) // 2
    signal_sub_band1 = signal_bandpass[:mid]
    signal_sub_band2 = signal_bandpass[mid:]
    
    return signal_sub_band1, signal_sub_band2

# Función para procesar audio y dividir en sub-bandas
def procesar_audio(file_path):
    with wave.open(file_path, 'rb') as wav:
        signal = np.frombuffer(wav.readframes(-1), dtype=np.int16)

    # Dividir la señal en sub-bandas
    sub_band1, sub_band2 = dividir_en_subbandas(signal, sampling_rate, 500, 2000)
    
    return sub_band1, sub_band2

# Función para procesar un directorio y obtener las energías promedio de las sub-bandas
def procesar_directorio(directorio):
    file_names = [os.path.join(directorio, file) for file in os.listdir(directorio) if file.endswith(".wav")]

    energies_sub_band1 = []
    energies_sub_band2 = []
    for file_name in file_names:
        signal_sub_band1, signal_sub_band2 = procesar_audio(file_name)
        
        energy_sub_band1 = calcular_energia(signal_sub_band1)
        energy_sub_band2 = calcular_energia(signal_sub_band2)
        
        energies_sub_band1.append(energy_sub_band1)
        energies_sub_band2.append(energy_sub_band2)

    mean_energy_sub_band1 = np.mean(energies_sub_band1)
    mean_energy_sub_band2 = np.mean(energies_sub_band2)
    std_energy_sub_band1 = np.std(energies_sub_band1)
    std_energy_sub_band2 = np.std(energies_sub_band2)

    # Calcular la FFT de las sub-bandas
    fft_sub_band1 = np.fft.fft(signal_sub_band1)
    fft_sub_band2 = np.fft.fft(signal_sub_band2)
    
    return mean_energy_sub_band1, mean_energy_sub_band2, std_energy_sub_band1, std_energy_sub_band2, fft_sub_band1, fft_sub_band2

# Procesar directorio "Arriba"
mean_energy_sub_band1_arriba, mean_energy_sub_band2_arriba, std_energy_sub_band1_arriba, std_energy_sub_band2_arriba, fft_sub_band1_arriba, fft_sub_band2_arriba = procesar_directorio("Arriba_procesado")

# Procesar directorio "Abajo"
mean_energy_sub_band1_abajo, mean_energy_sub_band2_abajo, std_energy_sub_band1_abajo, std_energy_sub_band2_abajo, fft_sub_band1_abajo, fft_sub_band2_abajo = procesar_directorio("Abajo_procesado")

# Grabar señal desde el micrófono
print(f"Grabando señal desde el micrófono por {duration} segundos a {sampling_rate} Hz ...")
recording = sd.rec(int(duration * sampling_rate), samplerate=sampling_rate, channels=1, dtype=np.int16)
sd.wait()

print("Procesando...")

# Obtener la señal del canal grabado
input_signal = recording.flatten()

# Separar la señal grabada en sub-bandas
input_sub_band1, input_sub_band2 = dividir_en_subbandas(input_signal, sampling_rate, 500, 2000)

# Calcular la energía de las sub-bandas de la señal grabada
energy_input_sub_band1 = calcular_energia(input_sub_band1)  
energy_input_sub_band2 = calcular_energia(input_sub_band2)

# Calcular la FFT de las sub-bandas de la señal grabada
fft_input_sub_band1 = np.fft.fft(input_sub_band1)
fft_input_sub_band2 = np.fft.fft(input_sub_band2)

# Imprimir energías promedio y desviaciones estándar de cada sub-banda
print("Energías y desviaciones estándar de cada sub-banda:")
print("---------------------------------------------------")
print("Para el directorio 'Arriba':")
print(f"Energía promedio de la primera sub-banda: {mean_energy_sub_band1_arriba}")
print(f"Energía promedio de la segunda sub-banda: {mean_energy_sub_band2_arriba}")
print(f"Desviación estándar de la primera sub-banda: {std_energy_sub_band1_arriba}")
print(f"Desviación estándar de la segunda sub-banda: {std_energy_sub_band2_arriba}")
print("---------------------------------------------------")
print("Para el directorio 'Abajo':")
print(f"Energía promedio de la primera sub-banda: {mean_energy_sub_band1_abajo}")
print(f"Energía promedio de la segunda sub-banda: {mean_energy_sub_band2_abajo}")
print(f"Desviación estándar de la primera sub-banda: {std_energy_sub_band1_abajo}")
print(f"Desviación estándar de la segunda sub-banda: {std_energy_sub_band2_abajo}")
print("---------------------------------------------------")

# Imprimir energías de las sub-bandas de la señal grabada
print("Energías de las sub-bandas de la señal grabada:")
print("---------------------------------------------------")
print(f"Energía de la primera sub-banda: {energy_input_sub_band1}")
print(f"Energía de la segunda sub-banda: {energy_input_sub_band2}")
print("---------------------------------------------------")

# Comparar las energías promedio de los directorios con las del audio grabado
diferencia_arriba_sub_band1 = abs(mean_energy_sub_band1_arriba - energy_input_sub_band1)
diferencia_arriba_sub_band2 = abs(mean_energy_sub_band2_arriba - energy_input_sub_band2)
diferencia_abajo_sub_band1 = abs(mean_energy_sub_band1_abajo - energy_input_sub_band1)
diferencia_abajo_sub_band2 = abs(mean_energy_sub_band2_abajo - energy_input_sub_band2)

print("Comparaciones de las energías promedio con el audio grabado:")
print("---------------------------------------------------")
print("Para el directorio 'Arriba':")
print(f"Diferencia de la primera sub-banda: {diferencia_arriba_sub_band1}")
print(f"Diferencia de la segunda sub-banda: {diferencia_arriba_sub_band2}")
print("---------------------------------------------------")
print("Para el directorio 'Abajo':")
print(f"Diferencia de la primera sub-banda: {diferencia_abajo_sub_band1}")
print(f"Diferencia de la segunda sub-banda: {diferencia_abajo_sub_band2}")
print("---------------------------------------------------")

# Calcular diferencias entre las energías promedio de cada sub-banda y las del audio grabado
diferencia_arriba = (abs(mean_energy_sub_band1_arriba - energy_input_sub_band1) + abs(mean_energy_sub_band2_arriba - energy_input_sub_band2)) / 2
diferencia_abajo = (abs(mean_energy_sub_band1_abajo - energy_input_sub_band1) + abs(mean_energy_sub_band2_abajo - energy_input_sub_band2)) / 2

# Determinar cuál palabra está más cerca
if diferencia_arriba < diferencia_abajo:
    palabra_mas_cerca = "Arriba"
else:
    palabra_mas_cerca = "Abajo"

print(f"La palabra más cercana al audio grabado es: {palabra_mas_cerca}")
print(f"Diferencia promedio para 'Arriba': {diferencia_arriba}")
print(f"Diferencia promedio para 'Abajo': {diferencia_abajo}")

# Mostrar las FFT de las sub-bandas de cada directorio en una sola ventana
plt.figure(figsize=(10, 6))

plt.subplot(2, 2, 1)
plt.plot(np.abs(fft_input_sub_band1))
plt.title('FFT - Sub-banda 1 (Señal Grabada)')
plt.xlabel('Frecuencia')
plt.ylabel('Magnitud')

plt.subplot(2, 2, 2)
plt.plot(np.abs(fft_input_sub_band2))
plt.title('FFT - Sub-banda 2 (Señal Grabada)')
plt.xlabel('Frecuencia')
plt.ylabel('Magnitud')

plt.subplot(2, 2, 3)
plt.plot(np.abs(fft_sub_band1_arriba))
plt.title('FFT - Sub-banda 1 (Arriba)')
plt.xlabel('Frecuencia')
plt.ylabel('Magnitud')

plt.subplot(2, 2, 4)
plt.plot(np.abs(fft_sub_band2_arriba))
plt.title('FFT - Sub-banda 2 (Arriba)')
plt.xlabel('Frecuencia')
plt.ylabel('Magnitud')

plt.tight_layout()
plt.show()

plt.figure(figsize=(10, 6))

plt.subplot(2, 2, 1)
plt.plot(np.abs(fft_sub_band1_abajo))
plt.title('FFT - Sub-banda 1 (Abajo)')
plt.xlabel('Frecuencia')
plt.ylabel('Magnitud')

plt.subplot(2, 2, 2)
plt.plot(np.abs(fft_sub_band2_abajo))
plt.title('FFT - Sub-banda 2 (Abajo)')
plt.xlabel('Frecuencia')
plt.ylabel('Magnitud')

plt.subplot(2, 2, 3)
plt.plot(np.abs(fft_input_sub_band1))
plt.title('FFT - Sub-banda 1 (Señal Grabada)')
plt.xlabel('Frecuencia')
plt.ylabel('Magnitud')

plt.subplot(2, 2, 4)
plt.plot(np.abs(fft_input_sub_band2))
plt.title('FFT - Sub-banda 2 (Señal Grabada)')
plt.xlabel('Frecuencia')
plt.ylabel('Magnitud')

plt.tight_layout()
plt.show()
