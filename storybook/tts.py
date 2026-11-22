"""Narración con voz sintética local (Piper TTS)."""
from __future__ import annotations

import wave
from pathlib import Path

from .audio_utils import wav_duration
from .config import TTSConfig


def ensure_voice_files(cfg: TTSConfig) -> tuple[str, str]:
    """Descarga (si hace falta) y devuelve las rutas locales del modelo .onnx y su .json."""
    from huggingface_hub import hf_hub_download

    onnx = hf_hub_download(cfg.voice_repo, cfg.voice_path + ".onnx")
    conf = hf_hub_download(cfg.voice_repo, cfg.voice_path + ".onnx.json")
    return onnx, conf


class Narrator:
    def __init__(self, cfg: TTSConfig):
        self.cfg = cfg
        self.voice = None

    def load(self):
        from piper import PiperVoice

        onnx, conf = ensure_voice_files(self.cfg)
        self.voice = PiperVoice.load(onnx, config_path=conf)
        return self

    def synthesize(self, text: str, out_path) -> float:
        """Sintetiza `text` a un WAV y devuelve su duración en segundos."""
        out_path = Path(out_path)
        last = None
        for _ in range(2):
            try:
                with wave.open(str(out_path), "wb") as wf:
                    if hasattr(self.voice, "synthesize_wav"):  # piper-tts >= 1.3
                        self.voice.synthesize_wav(text, wf)
                    else:  # piper-tts 1.2.x
                        self.voice.synthesize(text, wf)
                return wav_duration(out_path)
            except Exception as e:  # noqa: BLE001
                last = e
        raise RuntimeError(f"No se pudo sintetizar la voz: {last}")
