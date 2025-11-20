"""
Utilidades de audio: grabación, carga de WAV y dispositivos de entrada.
"""

import os
from typing import Tuple, Dict
import numpy as np
import sounddevice as sd
import soundfile as sf


def ensure_dir(d: str):
    if not os.path.exists(d):
        os.makedirs(d)


def record_fixed_length(filename: str, duration_s: float, fs: int, device: int | None = None):
    data = sd.rec(int(duration_s * fs), samplerate=fs, channels=1, dtype='float32', device=device)
    sd.wait()
    x = data.flatten()
    sf.write(filename, x, fs)


def load_and_prepare_wav(path: str, N: int) -> np.ndarray:
    x, fsf = sf.read(path, dtype='float32')
    if x.ndim > 1:
        x = x.mean(axis=1)
    x = x[:N]
    if x.size < N:
        x = np.pad(x, (0, N - x.size))
    return x


def enumerate_input_devices() -> tuple[list, Dict[int, str]]:
    try:
        devices = sd.query_devices()
        hostapis_info = sd.query_hostapis()
        hostapis = {i: h['name'] for i, h in enumerate(hostapis_info)}
        return [d for d in devices if d.get('max_input_channels', 0) > 0], hostapis
    except Exception:
        return [], {}


def parse_device_index(label: str) -> int | None:
    try:
        return int(label.split(":")[0]) if ":" in label else None
    except Exception:
        return None
