"""
Script de validación del modelo de reconocimiento de voz
Verifica que el error sea máximo del 5%
"""

import os
import numpy as np
import soundfile as sf
from model_utils import load_model, decide_label_by_min_dist
from dsp_utils import compute_subband_energies
from audio_utils import load_and_prepare_wav


def validar_modelo(model_path: str = "lab5_model.json", 
                   recordings_dir: str = "recordings",
                   max_samples_per_command: int = None):
    """
    Valida el modelo con archivos de prueba.
    
    Args:
        model_path: Ruta al modelo entrenado
        recordings_dir: Directorio con las grabaciones
        max_samples_per_command: Número máximo de muestras a probar por comando (None = todas)
    
    Returns:
        dict con resultados de validación
    """
    
    print("="*80)
    print("VALIDACIÓN DEL MODELO DE RECONOCIMIENTO")
    print("="*80)
    
    # Cargar modelo
    print(f"\n📂 Cargando modelo: {model_path}")
    model = load_model(model_path)
    
    fs = model['fs']
    N = model['N']
    K = model['K']
    window = model['window']
    commands = list(model['commands'].keys())
    
    print(f"✓ Modelo cargado exitosamente")
    print(f"  Comandos: {', '.join(commands)}")
    print(f"  Parámetros: fs={fs} Hz, N={N}, K={K} segmentos, ventana={window}")
    
    # Recolectar archivos de prueba
    print(f"\n📁 Buscando archivos de prueba en: {recordings_dir}/")
    
    test_files = []
    for command in commands:
        folder = os.path.join(recordings_dir, command)
        if not os.path.exists(folder):
            print(f"⚠️  No existe la carpeta: {folder}")
            continue
        
        wavs = [f for f in os.listdir(folder) if f.lower().endswith('.wav')]
        if max_samples_per_command:
            wavs = wavs[:max_samples_per_command]
        
        for wav_file in wavs:
            filepath = os.path.join(folder, wav_file)
            test_files.append((filepath, command))
        
        print(f"  • {command}: {len(wavs)} archivos")
    
    total_files = len(test_files)
    print(f"\n📊 Total de archivos a validar: {total_files}")
    
    if total_files == 0:
        print("❌ No hay archivos para validar")
        return None
    
    # Realizar pruebas
    print(f"\n{'='*80}")
    print("EJECUTANDO VALIDACIÓN")
    print(f"{'='*80}\n")
    
    results = {
        'correct': 0,
        'incorrect': 0,
        'errors': 0,
        'total': total_files,
        'predictions': [],
        'confusion_matrix': {cmd: {c: 0 for c in commands} for cmd in commands}
    }
    
    for i, (filepath, expected) in enumerate(test_files, 1):
        try:
            # Cargar y procesar audio
            x = load_and_prepare_wav(filepath, N)
            x_orig, _ = sf.read(filepath)
            if x_orig.ndim > 1:
                x_orig = x_orig.mean(axis=1)
            
            # Extraer características
            Es, bands, freqs = compute_subband_energies(x, fs, N, K, window)
            
            # Reconocer
            predicted, dists = decide_label_by_min_dist(Es, model, x_raw=x_orig)
            
            # Evaluar
            is_correct = (predicted == expected)
            
            if is_correct:
                results['correct'] += 1
                status = "✅"
            else:
                results['incorrect'] += 1
                status = "❌"
            
            # Matriz de confusión
            results['confusion_matrix'][expected][predicted] += 1
            
            # Guardar resultado
            results['predictions'].append({
                'file': filepath,
                'expected': expected,
                'predicted': predicted,
                'correct': is_correct,
                'distances': dists
            })
            
            # Mostrar progreso (solo algunos)
            if i <= 10 or i % 10 == 0 or not is_correct:
                dist_str = ', '.join([f'{k}={v:.3f}' for k, v in sorted(dists.items(), key=lambda x: x[1])])
                print(f"{status} [{i}/{total_files}] {os.path.basename(filepath)}")
                print(f"     Esperado: '{expected}' | Predicho: '{predicted}' | Distancias: {dist_str}")
            
        except Exception as e:
            results['errors'] += 1
            print(f"❌ [{i}/{total_files}] Error en {filepath}: {e}")
    
    # Calcular métricas
    accuracy = results['correct'] / results['total'] * 100
    error_rate = results['incorrect'] / results['total'] * 100
    
    # Mostrar resultados
    print(f"\n{'='*80}")
    print("RESULTADOS DE VALIDACIÓN")
    print(f"{'='*80}")
    
    print(f"\n📊 Resumen:")
    print(f"  Total de muestras:    {results['total']}")
    print(f"  Correctas:            {results['correct']}")
    print(f"  Incorrectas:          {results['incorrect']}")
    print(f"  Errores de lectura:   {results['errors']}")
    
    print(f"\n📈 Métricas:")
    print(f"  Precisión (Accuracy): {accuracy:.2f}%")
    print(f"  Tasa de Error:        {error_rate:.2f}%")
    
    # Verificar umbral del 5%
    print(f"\n🎯 Verificación de requisito:")
    if error_rate <= 5.0:
        print(f"  ✅ CUMPLE: La tasa de error ({error_rate:.2f}%) es menor o igual al 5%")
    else:
        print(f"  ❌ NO CUMPLE: La tasa de error ({error_rate:.2f}%) supera el 5% permitido")
        print(f"     Se necesita mejorar en {error_rate - 5.0:.2f} puntos porcentuales")
    
    # Matriz de confusión
    print(f"\n📋 Matriz de Confusión:")
    print(f"{'':>15} | " + " | ".join([f"{cmd:>12}" for cmd in commands]))
    print("-" * (15 + len(commands) * 15))
    
    for true_cmd in commands:
        row = f"{true_cmd:>15} | "
        row += " | ".join([f"{results['confusion_matrix'][true_cmd][pred]:>12}" for pred in commands])
        print(row)
    
    # Análisis por comando
    print(f"\n📊 Precisión por comando:")
    for cmd in commands:
        total_cmd = sum(results['confusion_matrix'][cmd].values())
        correct_cmd = results['confusion_matrix'][cmd][cmd]
        if total_cmd > 0:
            acc_cmd = correct_cmd / total_cmd * 100
            print(f"  {cmd:>12}: {acc_cmd:5.1f}% ({correct_cmd}/{total_cmd})")
    
    # Casos incorrectos
    if results['incorrect'] > 0:
        print(f"\n⚠️  Casos incorrectos ({results['incorrect']}):")
        for pred in results['predictions']:
            if not pred['correct']:
                print(f"  • {os.path.basename(pred['file'])}")
                print(f"    Esperado: '{pred['expected']}' | Predicho: '{pred['predicted']}'")
                dist_str = ', '.join([f"{k}={v:.3f}" for k, v in sorted(pred['distances'].items(), key=lambda x: x[1])])
                print(f"    Distancias: {dist_str}")
    
    print(f"\n{'='*80}")
    
    return results


def validacion_cruzada(recordings_dir: str = "recordings", 
                       k_folds: int = 5,
                       model_params: dict = None):
    """
    Realiza validación cruzada k-fold para evaluar robustez del modelo.
    
    Args:
        recordings_dir: Directorio con grabaciones
        k_folds: Número de particiones para validación cruzada
        model_params: Parámetros del modelo (si None, usa valores por defecto)
    
    Returns:
        dict con resultados de validación cruzada
    """
    from model_utils import train_from_folder
    import tempfile
    
    if model_params is None:
        model_params = {
            'fs': 44100,
            'N': 4096,
            'K': 10,
            'window': 'hamming'
        }
    
    print("="*80)
    print("VALIDACIÓN CRUZADA K-FOLD")
    print("="*80)
    print(f"K-folds: {k_folds}")
    print(f"Parámetros: {model_params}")
    
    # Recolectar todos los archivos por comando
    commands = {}
    for subdir in os.listdir(recordings_dir):
        folder = os.path.join(recordings_dir, subdir)
        if os.path.isdir(folder):
            wavs = [os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith('.wav')]
            if len(wavs) > 0:
                commands[subdir] = wavs
    
    print(f"\nComandos encontrados: {list(commands.keys())}")
    
    fold_results = []
    
    for fold in range(k_folds):
        print(f"\n{'='*80}")
        print(f"FOLD {fold + 1}/{k_folds}")
        print(f"{'='*80}")
        
        # Dividir datos en entrenamiento y prueba
        # TODO: Implementar división y entrenamiento por fold
        
        pass
    
    # TODO: Calcular métricas promedio y desviación estándar
    
    return fold_results


if __name__ == "__main__":
    import sys
    
    # Modo de uso
    if len(sys.argv) > 1:
        if sys.argv[1] == "--cv":
            # Validación cruzada
            validacion_cruzada()
        elif sys.argv[1] == "--help":
            print("Uso:")
            print("  python validar.py           - Validación estándar")
            print("  python validar.py --cv      - Validación cruzada")
            print("  python validar.py --quick   - Validación rápida (10 muestras/comando)")
        elif sys.argv[1] == "--quick":
            validar_modelo(max_samples_per_command=10)
        else:
            validar_modelo()
    else:
        # Validación estándar
        validar_modelo()
