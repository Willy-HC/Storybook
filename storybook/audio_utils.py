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


def scaled_wav_bytes(path, gain: float) -> bytes:
    """Devuelve el WAV con su volumen multiplicado por `gain` (0-1), listo para st.audio."""
    import io

    with wave.open(str(path), "rb") as wf:
        params = wf.getparams()
        frames = wf.readframes(wf.getnframes())
    if params.sampwidth != 2:
        return Path(path).read_bytes()
    x = np.frombuffer(frames, dtype="<i2").astype(np.float32) * float(gain)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as out:
        out.setnchannels(params.nchannels)
        out.setsampwidth(2)
        out.setframerate(params.framerate)
        out.writeframes(np.clip(x, -32768, 32767).astype("<i2").tobytes())
    return buf.getvalue()
