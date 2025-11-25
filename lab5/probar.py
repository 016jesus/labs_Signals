"""
Script de prueba rápida del sistema de reconocimiento
"""

import soundfile as sf
import numpy as np
from model_utils import load_model, decide_label_by_min_dist
from dsp_utils import compute_subband_energies

# Cargar modelo
print("Cargando modelo...")
model = load_model("lab5_model.json")

fs = model['fs']
N = model['N']
K = model['K']
window = model['window']

print(f"Modelo cargado: {len(model['commands'])} comandos")
print(f"Parámetros: fs={fs}, N={N}, K={K}, window={window}")

# Probar con archivos de prueba
test_files = [
    ("recordings/segmentar/Audio 1-10.wav", "segmentar"),
    ("recordings/cifrar/Audio 1-10.wav", "cifrar"),
    ("recordings/comprimir/Audio 1-10.wav", "comprimir"),
]

print("\n" + "="*70)
print("PRUEBAS DE RECONOCIMIENTO")
print("="*70)

correct = 0
total = 0

for filepath, expected in test_files:
    try:
        # Cargar audio
        x, fs_file = sf.read(filepath)
        if x.ndim > 1:
            x = x.mean(axis=1)
        
        x_orig = x.copy()
        
        # Preparar ventana
        if len(x) < N:
            x = np.pad(x, (0, N - len(x)), mode='constant')
        else:
            x = x[:N]
        
        # Extraer características FFT
        Es, bands, freqs = compute_subband_energies(x, fs, N, K, window)
        
        # Reconocer (usa DTW internamente)
        label, dists = decide_label_by_min_dist(Es, model, x_raw=x_orig)
        
        # Resultados
        is_correct = (label == expected)
        correct += is_correct
        total += 1
        
        status = "✅" if is_correct else "❌"
        print(f"\n{status} Archivo: {filepath}")
        print(f"   Esperado: '{expected}'")
        print(f"   Predicho: '{label}'")
        print(f"   Distancias: {', '.join([f'{k}={v:.3f}' for k, v in sorted(dists.items(), key=lambda x: x[1])])}")
        
    except Exception as e:
        print(f"\n❌ Error con {filepath}: {e}")
        total += 1

print("\n" + "="*70)
print(f"RESULTADO: {correct}/{total} correctos ({correct/total*100:.1f}%)")
print("="*70)

if correct == total:
    print("✅ ¡Todas las pruebas pasaron!")
else:
    print(f"⚠️  Algunas pruebas fallaron. Precisión: {correct/total*100:.1f}%")
