"""
Ejemplo simplificado del método de reconocimiento por bandas de frecuencia
============================================================================

Este script muestra el concepto básico del reconocimiento sin la complejidad
del sistema completo.
"""

import numpy as np
from scipy.signal import get_window

# Parámetros
FS = 44100  # Frecuencia de muestreo
N = 4096    # Tamaño FFT
K = 10      # Número de bandas


def dividir_en_bandas(X, K):
    """
    Divide el espectro X en K bandas iguales.
    
    Args:
        X: Espectro FFT (array de N//2 + 1 valores complejos)
        K: Número de bandas
    
    Returns:
        Lista de K bandas, cada una es un segmento del espectro
    """
    num_bins = len(X)
    tamaño_banda = num_bins // K
    
    bandas = []
    for i in range(K):
        inicio = i * tamaño_banda
        fin = (i + 1) * tamaño_banda if i < K - 1 else num_bins
        banda = X[inicio:fin]
        bandas.append(banda)
    
    return bandas


def calcular_energias(audio, fs=FS, n=N, k=K):
    """
    PASO A PASO: Calcular energías por banda de frecuencia.
    
    Args:
        audio: Señal de audio (numpy array)
        fs: Frecuencia de muestreo
        n: Tamaño de ventana FFT
        k: Número de bandas
    
    Returns:
        Array de K energías, una por cada banda
    """
    
    print(f"🎵 Audio original: {len(audio)} muestras")
    
    # PASO 1: Preparar audio
    if len(audio) < n:
        audio = np.pad(audio, (0, n - len(audio)))
    else:
        audio = audio[:n]
    
    print(f"📏 Audio ajustado: {n} muestras")
    
    # PASO 2: Aplicar ventana
    ventana = get_window("hamming", n)
    audio_ventaneado = audio * ventana
    print(f"🪟 Ventana aplicada: Hamming")
    
    # PASO 3: Calcular FFT
    X = np.fft.rfft(audio_ventaneado, n=n)
    print(f"🔢 FFT calculada: {len(X)} bins de frecuencia")
    
    # PASO 4: Dividir en K bandas
    bandas = dividir_en_bandas(X, k)
    print(f"📊 Espectro dividido en {k} bandas")
    
    # PASO 5: Calcular energía de cada banda
    energias = []
    freqs = np.fft.rfftfreq(n, d=1.0/fs)
    
    print(f"\n{'='*60}")
    print(f"ENERGÍAS POR BANDA:")
    print(f"{'='*60}")
    
    for i, banda in enumerate(bandas):
        # Energía = suma de las magnitudes al cuadrado
        energia = np.sum(np.abs(banda) ** 2)
        energias.append(energia)
        
        # Calcular rango de frecuencias de esta banda
        idx_inicio = i * (len(X) // k)
        idx_fin = min((i + 1) * (len(X) // k), len(X) - 1)
        f_min = freqs[idx_inicio]
        f_max = freqs[idx_fin]
        
        print(f"Banda {i+1:2d}: [{f_min:7.1f} - {f_max:7.1f} Hz]  →  Energía = {energia:12.2f}")
    
    print(f"{'='*60}\n")
    
    # PASO 6: Normalizar
    energias = np.array(energias)
    energias = np.log10(energias + 1e-10)  # Escala logarítmica
    energias = energias / np.sum(energias)  # Normalizar a suma=1
    
    return energias


def comparar_con_patrones(energias, patrones):
    """
    Compara las energías con los patrones de cada comando.
    
    Args:
        energias: Vector de K energías del audio a reconocer
        patrones: Diccionario {comando: vector_de_energías}
    
    Returns:
        Comando reconocido
    """
    print(f"🔍 COMPARANDO CON PATRONES:")
    print(f"{'='*60}")
    
    distancias = {}
    
    for comando, patron in patrones.items():
        # Distancia euclidiana
        distancia = np.linalg.norm(energias - patron)
        distancias[comando] = distancia
        
        print(f"{comando:12s}: distancia = {distancia:.4f}")
    
    print(f"{'='*60}\n")
    
    # El comando con menor distancia gana
    comando_reconocido = min(distancias, key=distancias.get)
    
    return comando_reconocido, distancias


def ejemplo_completo():
    """
    Ejemplo completo de reconocimiento.
    """
    print("\n" + "="*70)
    print("EJEMPLO: RECONOCIMIENTO POR BANDAS DE FRECUENCIA")
    print("="*70 + "\n")
    
    # Simular audio de 1 segundo
    duracion = 1.0
    t = np.linspace(0, duracion, int(FS * duracion))
    
    # Generar señal de prueba (mezcla de frecuencias)
    # Simulamos diferentes palabras con diferentes combinaciones de frecuencias
    audio_prueba = (np.sin(2 * np.pi * 300 * t) +      # Frecuencia baja
                    0.5 * np.sin(2 * np.pi * 1500 * t) + # Frecuencia media
                    0.3 * np.sin(2 * np.pi * 4000 * t))  # Frecuencia alta
    
    print("📢 Calculando energías del audio de prueba...")
    print("-" * 60)
    
    energias = calcular_energias(audio_prueba)
    
    # Patrones de ejemplo (normalmente vienen del entrenamiento)
    print("📚 Patrones de comandos (ejemplo simulado):")
    print("-" * 60)
    patrones = {
        "segmentar":  np.array([0.12, 0.28, 0.19, 0.17, 0.24, 0.10, 0.15, 0.08, 0.12, 0.05]),
        "cifrar":     np.array([0.25, 0.15, 0.35, 0.10, 0.15, 0.20, 0.08, 0.12, 0.18, 0.07]),
        "comprimir":  np.array([0.08, 0.40, 0.18, 0.12, 0.22, 0.15, 0.10, 0.09, 0.14, 0.06]),
    }
    
    for cmd, pat in patrones.items():
        print(f"{cmd:12s}: {pat}")
    print()
    
    # Reconocer
    comando, dists = comparar_con_patrones(energias, patrones)
    
    print("✅ RESULTADO:")
    print("="*70)
    print(f"Comando reconocido: {comando.upper()}")
    print(f"Distancia: {dists[comando]:.4f}")
    print("="*70 + "\n")


def mostrar_concepto():
    """
    Muestra el concepto de manera visual y simple.
    """
    print("\n" + "="*70)
    print("CONCEPTO BÁSICO")
    print("="*70)
    print("""
El reconocimiento funciona así:

1. DIVISIÓN EN BANDAS:
   Espectro [0 - 22050 Hz] → K=10 bandas
   
   Banda 1:  [    0 -  2205 Hz]  Graves
   Banda 2:  [ 2205 -  4410 Hz]
   Banda 3:  [ 4410 -  6615 Hz]
   ...
   Banda 10: [19845 - 22050 Hz]  Agudas

2. CÁLCULO DE ENERGÍA:
   Para cada banda:
     Energía = Σ |X(f)|²
   
   Donde X(f) es la FFT en esa banda

3. PATRÓN CARACTERÍSTICO:
   Cada palabra tiene una "firma" de energías:
   
   "segmentar"  = [E₁, E₂, E₃, ..., E₁₀]
   "cifrar"     = [E₁, E₂, E₃, ..., E₁₀]
   "comprimir"  = [E₁, E₂, E₃, ..., E₁₀]

4. RECONOCIMIENTO:
   - Calcular energías del audio nuevo
   - Comparar con cada patrón (distancia euclidiana)
   - El más cercano es el comando reconocido

Ejemplo visual con K=10:

       Energía por banda
       
"segmentar"  ████░░████████░░░░█████░░░░░░
"cifrar"     ████████░░░░███░░░░░░░░░█████
"comprimir"  ░░░░████████░░░░█████░░░░░░░░

Cada barra representa la energía en esa banda de frecuencia.
    """)
    print("="*70 + "\n")


if __name__ == "__main__":
    # Mostrar concepto
    mostrar_concepto()
    
    # Ejecutar ejemplo
    ejemplo_completo()
    
    print("\n💡 TIP:")
    print("   Este es un ejemplo simplificado. El sistema completo incluye:")
    print("   - Preprocesamiento de audio (normalización, pre-énfasis)")
    print("   - Entrenamiento con múltiples muestras")
    print("   - Validación estadística")
    print("   - Visualización en tiempo real")
    print("\n   Ejecuta 'python main.py' para ver el sistema completo.\n")
