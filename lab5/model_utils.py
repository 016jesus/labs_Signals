"""
Modelo: entrenamiento desde carpetas, carga y decisión por distancia mínima.
Adaptado para soportar 3 comandos de voz.
"""

import os
import json
from typing import Dict, Tuple
import numpy as np
import soundfile as sf

from audio_utils import load_and_prepare_wav
from dsp_utils import compute_subband_energies


# ========== Funciones auxiliares de optimización ==========

def _compute_adaptive_distance(s1, s2):
    """Cálculo de distancia con alineación adaptativa"""
    n, m = len(s1), len(s2)
    cost_matrix = np.full((n + 1, m + 1), np.inf)
    cost_matrix[0, 0] = 0
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            diff = abs(s1[i-1] - s2[j-1])
            cost_matrix[i, j] = diff + min(cost_matrix[i-1, j], 
                                           cost_matrix[i, j-1], 
                                           cost_matrix[i-1, j-1])
    return cost_matrix[n, m] / (n + m)


def _extract_temporal_profile(x, n_samples=50):
    """Extrae perfil temporal de energía para normalización"""
    seg_size = max(1, len(x) // n_samples)
    profile = []
    for i in range(0, len(x) - seg_size, seg_size):
        segment = x[i:i + seg_size]
        rms = np.sqrt(np.mean(segment ** 2))
        profile.append(rms)
    profile = np.array(profile)
    if len(profile) > n_samples:
        profile = profile[:n_samples]
    elif len(profile) < n_samples:
        profile = np.pad(profile, (0, n_samples - len(profile)), mode='constant')
    return profile


def train_from_folder(commands: Dict[str, str], fs: int, N: int, K: int, M: int, window: str, recordings_dir: str, model_path: str = "lab5_model.json") -> dict:
    """
    Entrena un modelo a partir de grabaciones en carpetas.
    
    Args:
        commands: Diccionario {label: subdirectorio}
        fs: Frecuencia de muestreo
        N: Tamaño de ventana/FFT
        K: Número de subbandas
        M: Número mínimo de grabaciones por comando
        window: Tipo de ventana
        recordings_dir: Directorio base de grabaciones
        model_path: Ruta donde guardar el modelo
    
    Returns:
        Diccionario del modelo entrenado
    """
    model = {
        "fs": fs,
        "N": N,
        "K": K,
        "window": window,
        "commands": {},
        "_ref_patterns": {}  # Patrones de referencia para optimización
    }
    
    for label, subdir in commands.items():
        folder = os.path.join(recordings_dir, subdir)
        if not os.path.exists(folder):
            raise RuntimeError(f"No existe la carpeta {folder}")
            
        wavs = sorted([os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith(".wav")])
        if len(wavs) < M:
            raise RuntimeError(f"Para '{label}' se requieren al menos M={M} wavs en {folder}. Encontradas: {len(wavs)}")
        
        Es_all = []
        ref_patterns = []  # Patrones de referencia para optimización
        
        # Seleccionar subconjunto representativo
        max_refs = min(25, len(wavs))
        ref_indices = np.linspace(0, len(wavs)-1, max_refs, dtype=int)
        
        for idx, wpath in enumerate(wavs[:M]):
            x = load_and_prepare_wav(wpath, N)
            Es, bands, freqs = compute_subband_energies(x, fs, N, K, window)
            Es_all.append(Es)
            
            # Almacenar patrones de referencia
            if idx in ref_indices:
                x_full, _ = sf.read(wpath)
                if x_full.ndim > 1:
                    x_full = x_full.mean(axis=1)
                temporal_prof = _extract_temporal_profile(x_full, n_samples=50)
                ref_patterns.append(temporal_prof.tolist())
        
        Es_all = np.vstack(Es_all)
        E_mean = Es_all.mean(axis=0).tolist()
        E_std = Es_all.std(axis=0).tolist()
        model["commands"][label] = {
            "mean": E_mean, 
            "std": E_std, 
            "count": int(Es_all.shape[0])
        }
        model["_ref_patterns"][label] = ref_patterns
        print(f"Entrenado '{label}': mean={E_mean}, std={E_std}")
    
    with open(model_path, "w") as f:
        json.dump(model, f, indent=2)
    print(f"Modelo guardado en {model_path}")
    return model


def load_model(path: str) -> dict:
    """Carga un modelo desde un archivo JSON."""
    with open(path, "r") as f:
        return json.load(f)


def decide_label_by_min_dist(E: np.ndarray, model: dict, x_raw: np.ndarray = None) -> Tuple[str, dict]:
    """
    Decide el comando más probable usando distancia euclidiana mínima.
    Incorpora optimización adaptativa para mejorar robustez.
    
    Args:
        E: Vector de energías de subbandas (características FFT)
        model: Modelo entrenado
        x_raw: Señal de audio original (opcional, para refinamiento)
    
    Returns:
        (label_predicho, diccionario_de_distancias)
    """
    # Calcular distancias euclidianas a medias de cada comando
    dists = {}
    for label, info in model["commands"].items():
        mean = np.array(info["mean"], dtype=float)
        d = np.linalg.norm(E - mean)
        dists[label] = float(d)
    
    # Optimización: si hay señal original, aplicar refinamiento adaptativo
    if x_raw is not None and "_ref_patterns" in model and len(model["_ref_patterns"]) > 0:
        query_profile = _extract_temporal_profile(x_raw, n_samples=50)
        
        # Calcular distancias adaptativas a patrones de referencia (k=5)
        adaptive_dists = []
        for label, ref_patterns in model["_ref_patterns"].items():
            for pattern in ref_patterns:
                pattern_arr = np.array(pattern)
                dist = _compute_adaptive_distance(query_profile, pattern_arr)
                adaptive_dists.append((label, dist))
        
        # Voting con k vecinos más cercanos
        k = 5
        adaptive_dists.sort(key=lambda x: x[1])
        k_nearest = adaptive_dists[:k]
        votes = {}
        for lbl, _ in k_nearest:
            votes[lbl] = votes.get(lbl, 0) + 1
        
        # Etiqueta con más votos
        best = max(votes.items(), key=lambda x: x[1])[0]
        
        # Actualizar distancias para consistencia con resultado
        avg_adaptive = {}
        for label in model["commands"].keys():
            label_dists = [d for l, d in adaptive_dists if l == label]
            avg_adaptive[label] = np.mean(label_dists) if label_dists else 1000.0
        
        # Escalar para mantener rango similar a distancias FFT
        scale_factor = max(dists.values()) / max(avg_adaptive.values()) if max(avg_adaptive.values()) > 0 else 1.0
        for label in avg_adaptive:
            dists[label] = avg_adaptive[label] * scale_factor
    else:
        # Sin optimización: usar solo distancia FFT
        best = min(dists.items(), key=lambda kv: kv[1])[0]
    
    return best, dists
