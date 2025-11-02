"""
Modelo: entrenamiento desde carpetas, carga y decisión por distancia mínima.
"""

import os
import json
from typing import Dict, Tuple
import numpy as np

from audio_utils import load_and_prepare_wav
from dsp_utils import compute_subband_energies


def train_from_folder(commands: Dict[str, str], fs: int, N: int, K: int, M: int, window: str, recordings_dir: str, model_path: str = "lab2_model.json") -> dict:
    model = {
        "fs": fs,
        "N": N,
        "K": K,
        "window": window,
        "commands": {}
    }
    for label, subdir in commands.items():
        folder = os.path.join(recordings_dir, subdir)
        wavs = sorted([os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith(".wav")])
        if len(wavs) < M:
            raise RuntimeError(f"Para '{label}' se requieren al menos M={M} wavs en {folder}. Encontradas: {len(wavs)}")
        Es_all = []
        for wpath in wavs[:M]:
            x = load_and_prepare_wav(wpath, N)
            Es, bands, freqs = compute_subband_energies(x, fs, N, K, window)
            Es_all.append(Es)
        Es_all = np.vstack(Es_all)
        E_mean = Es_all.mean(axis=0).tolist()
        E_std = Es_all.std(axis=0).tolist()
        model["commands"][label] = {"mean": E_mean, "std": E_std, "count": int(Es_all.shape[0])}
        print(f"Entrenado '{label}': mean={E_mean}, std={E_std}")
    with open(model_path, "w") as f:
        json.dump(model, f, indent=2)
    print(f"Modelo guardado en {model_path}")
    return model


def load_model(path: str) -> dict:
    with open(path, "r") as f:
        return json.load(f)


def decide_label_by_min_dist(E: np.ndarray, model: dict) -> Tuple[str, dict]:
    dists = {}
    for label, info in model["commands"].items():
        mean = np.array(info["mean"], dtype=float)
        d = np.linalg.norm(E - mean)
        dists[label] = float(d)
    best = min(dists.items(), key=lambda kv: kv[1])[0]
    return best, dists
