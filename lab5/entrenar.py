"""
Script de entrenamiento simple para banco de filtros FFT
Laboratorio 5 - Reconocimiento de comandos de voz
"""

import os
import sys
from model_utils import train_from_folder

# Parámetros del sistema
FS = 44100         # Frecuencia de muestreo (Hz)
N = 4096           # Tamaño de ventana FFT
K = 10             # Número de subbandas espectrales
M = 50             # Muestras por comando
WINDOW = "hamming" # Tipo de ventana
MODEL_PATH = "lab5_model.json"
RECORDINGS_DIR = "recordings"

# Comandos a reconocer
commands = {
    "segmentar": "segmentar",
    "cifrar": "cifrar",
    "comprimir": "comprimir"
}

def main():
    print("="*70)
    print("ENTRENAMIENTO - Banco de Filtros FFT")
    print("="*70)
    print(f"\nParámetros:")
    print(f"  Frecuencia de muestreo: {FS} Hz")
    print(f"  Tamaño de ventana: {N} muestras ({N/FS*1000:.1f} ms)")
    print(f"  Número de subbandas: {K}")
    print(f"  Muestras por comando: {M}")
    print(f"  Tipo de ventana: {WINDOW}")
    print(f"\nDirectorio de grabaciones: {RECORDINGS_DIR}/")
    print(f"Archivo de salida: {MODEL_PATH}")
    
    # Verificar grabaciones
    print(f"\n{'-'*70}")
    print("Verificando grabaciones...")
    print(f"{'-'*70}")
    
    for label, subdir in commands.items():
        folder = os.path.join(RECORDINGS_DIR, subdir)
        if not os.path.exists(folder):
            print(f"❌ ERROR: No existe la carpeta {folder}")
            sys.exit(1)
        
        wavs = [f for f in os.listdir(folder) if f.lower().endswith('.wav')]
        print(f"  ✓ '{label}': {len(wavs)} archivos encontrados")
        
        if len(wavs) < M:
            print(f"    ⚠️  Solo hay {len(wavs)} grabaciones (se requieren {M})")
    
    # Entrenar
    print(f"\n{'-'*70}")
    print("Entrenando modelo...")
    print(f"{'-'*70}\n")
    
    try:
        model = train_from_folder(
            commands=commands,
            fs=FS,
            N=N,
            K=K,
            M=M,
            window=WINDOW,
            recordings_dir=RECORDINGS_DIR,
            model_path=MODEL_PATH
        )
        
        print(f"\n{'='*70}")
        print("✅ ENTRENAMIENTO COMPLETADO")
        print(f"{'='*70}")
        print(f"\nModelo guardado: {MODEL_PATH}")
        print(f"\nComandos entrenados:")
        for label, info in model['commands'].items():
            print(f"  • {label}: {info['count']} muestras")
        
        print(f"\n{'-'*70}")
        print("Siguiente paso:")
        print("  Ejecuta: python main.py")
        print("  Para probar el reconocimiento con la GUI")
        print(f"{'-'*70}\n")
        
    except Exception as e:
        print(f"\n❌ ERROR durante entrenamiento:")
        print(f"   {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
