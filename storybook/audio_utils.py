"""Utilidades para escribir y medir archivos WAV (solo NumPy + biblioteca estándar)."""
from __future__ import annotations

import wave
from pathlib import Path

import numpy as np


def write_wav(path, samples: np.ndarray, sr: int) -> Path:
    """Guarda audio mono float [-1, 1] como WAV de 16 bits."""
    path = Path(path)
    x = np.clip(np.asarray(samples, dtype=np.float32), -1.0, 1.0)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(int(sr))
        wf.writeframes((x * 32767).astype("<i2").tobytes())
    return path


def wav_duration(path) -> float:
    with wave.open(str(path), "rb") as wf:
        return wf.getnframes() / float(wf.getframerate())
