"""
Validación rápida con visualización de confianza
"""

import os
import numpy as np
import soundfile as sf
from model_utils import load_model, decide_label_by_min_dist
from dsp_utils import compute_subband_energies
from audio_utils import load_and_prepare_wav


def calculate_confidence(dists: dict) -> float:
    """
    Calcula la confianza basada en la separación entre predicciones.
    """
    if not dists or len(dists) < 2:
        return 0.0
    
    sorted_dists = sorted(dists.items(), key=lambda x: x[1])
    min_dist = sorted_dists[0][1]
    second_dist = sorted_dists[1][1]
    
    if second_dist > 0:
        separation_ratio = (second_dist - min_dist) / second_dist
        confidence = separation_ratio * 100
    else:
        confidence = 0.0
    
    # Penalizar distancias altas
    if min_dist > 0.3:
        confidence *= 0.5
    elif min_dist > 0.2:
        confidence *= 0.7
    
    return min(100.0, max(0.0, confidence))


def validar_rapido():
    """
    Validación rápida con algunos archivos de cada comando.
    """
    print("="*80)
    print("VALIDACIÓN RÁPIDA CON ANÁLISIS DE CONFIANZA")
    print("="*80)
    
    # Cargar modelo
    model_path = "lab5_model.json"
    print(f"\n📂 Cargando modelo: {model_path}")
    
    try:
        model = load_model(model_path)
    except Exception as e:
        print(f"❌ Error al cargar modelo: {e}")
        return
    
    fs = model['fs']
    N = model['N']
    K = model['K']
    window = model['window']
    commands = list(model['commands'].keys())
    
    print(f"✓ Modelo cargado")
    print(f"  Comandos: {', '.join(commands)}")
    
    # Archivos de prueba
    test_files = []
    for cmd in commands:
        folder = os.path.join("recordings", cmd)
        if os.path.exists(folder):
            wavs = [f for f in os.listdir(folder) if f.lower().endswith('.wav')][:5]  # 5 primeros
            for wav in wavs:
                test_files.append((os.path.join(folder, wav), cmd))
    
    print(f"\n📊 Probando {len(test_files)} archivos...\n")
    
    results = {
        'correct': 0,
        'incorrect': 0,
        'total': len(test_files),
        'confidences': [],
        'high_conf_correct': 0,
        'high_conf_total': 0
    }
    
    print(f"{'Archivo':<30} {'Esperado':<12} {'Predicho':<12} {'Confianza':<12} {'Estado':<15}")
    print("-"*80)
    
    for filepath, expected in test_files:
        try:
            # Cargar y procesar
            x = load_and_prepare_wav(filepath, N)
            x_orig, _ = sf.read(filepath)
            if x_orig.ndim > 1:
                x_orig = x_orig.mean(axis=1)
            
            # Extraer características y predecir
            Es, _, _ = compute_subband_energies(x, fs, N, K, window)
            predicted, dists = decide_label_by_min_dist(Es, model, x_raw=x_orig)
            
            # Calcular confianza
            confidence = calculate_confidence(dists)
            results['confidences'].append(confidence)
            
            # Evaluar
            is_correct = (predicted == expected)
            if is_correct:
                results['correct'] += 1
            else:
                results['incorrect'] += 1
            
            # Contar alta confianza
            if confidence >= 95.0:
                results['high_conf_total'] += 1
                if is_correct:
                    results['high_conf_correct'] += 1
            
            # Estado
            if is_correct:
                if confidence >= 95:
                    status = "✅ Correcto (Alta)"
                elif confidence >= 80:
                    status = "✅ Correcto (Media)"
                else:
                    status = "✅ Correcto (Baja)"
            else:
                status = "❌ INCORRECTO"
            
            # Formato de confianza
            conf_str = f"{confidence:.1f}%"
            if confidence >= 95:
                conf_display = f"🟢 {conf_str}"
            elif confidence >= 80:
                conf_display = f"🟡 {conf_str}"
            else:
                conf_display = f"🔴 {conf_str}"
            
            filename = os.path.basename(filepath)
            print(f"{filename:<30} {expected:<12} {predicted:<12} {conf_display:<20} {status:<15}")
            
        except Exception as e:
            print(f"{os.path.basename(filepath):<30} {'ERROR':<12} {'-':<12} {'-':<12} ❌ {str(e)[:20]}")
    
    # Resumen
    print("\n" + "="*80)
    print("RESUMEN DE RESULTADOS")
    print("="*80)
    
    accuracy = results['correct'] / results['total'] * 100
    error_rate = results['incorrect'] / results['total'] * 100
    avg_confidence = np.mean(results['confidences']) if results['confidences'] else 0.0
    
    print(f"\n📊 Métricas Generales:")
    print(f"  Total de muestras:     {results['total']}")
    print(f"  Correctas:             {results['correct']}")
    print(f"  Incorrectas:           {results['incorrect']}")
    print(f"  Precisión:             {accuracy:.2f}%")
    print(f"  Tasa de Error:         {error_rate:.2f}%")
    print(f"  Confianza Promedio:    {avg_confidence:.1f}%")
    
    print(f"\n🎯 Verificación de Requisito:")
    if error_rate <= 5.0:
        print(f"  ✅ CUMPLE: La tasa de error ({error_rate:.2f}%) es ≤ 5%")
    else:
        print(f"  ❌ NO CUMPLE: La tasa de error ({error_rate:.2f}%) supera el 5%")
        print(f"     Necesita mejorar {error_rate - 5.0:.2f} puntos porcentuales")
    
    # Análisis de confianza alta
    if results['high_conf_total'] > 0:
        high_conf_accuracy = results['high_conf_correct'] / results['high_conf_total'] * 100
        print(f"\n📈 Análisis de Alta Confianza (≥95%):")
        print(f"  Predicciones con alta confianza: {results['high_conf_total']}")
        print(f"  Correctas:                       {results['high_conf_correct']}")
        print(f"  Precisión con alta confianza:    {high_conf_accuracy:.1f}%")
    
    # Distribución de confianza
    if results['confidences']:
        print(f"\n📊 Distribución de Confianza:")
        high = sum(1 for c in results['confidences'] if c >= 95)
        medium = sum(1 for c in results['confidences'] if 80 <= c < 95)
        low = sum(1 for c in results['confidences'] if c < 80)
        
        print(f"  🟢 Alta (≥95%):    {high:2d} ({high/len(results['confidences'])*100:5.1f}%)")
        print(f"  🟡 Media (80-95%): {medium:2d} ({medium/len(results['confidences'])*100:5.1f}%)")
        print(f"  🔴 Baja (<80%):    {low:2d} ({low/len(results['confidences'])*100:5.1f}%)")
    
    print("\n" + "="*80)
    
    # Recomendaciones
    if error_rate > 5.0 or avg_confidence < 90:
        print("\n💡 Recomendaciones para mejorar:")
        if error_rate > 5.0:
            print("  • Aumentar el número de muestras de entrenamiento (M)")
            print("  • Mejorar la calidad de las grabaciones")
            print("  • Ajustar el número de segmentos (K)")
        if avg_confidence < 90:
            print("  • Las predicciones tienen baja confianza")
            print("  • Verificar que las grabaciones sean consistentes")
            print("  • Considerar agregar más características distintivas")
        print()


if __name__ == "__main__":
    validar_rapido()
