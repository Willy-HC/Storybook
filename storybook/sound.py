"""Ambientación sonora por escena: síntesis procedural (por defecto) o AudioLDM2 (opcional)."""
from __future__ import annotations

import gc
from pathlib import Path

import numpy as np

from . import procedural_audio
from .audio_utils import write_wav
from .config import SoundConfig


class SoundGenerator:
    def __init__(self, cfg: SoundConfig, log=print):
        self.cfg = cfg
        self.log = log
        self.pipe = None
        self.device = "cpu"

    def load(self):
        if self.cfg.backend != "audioldm2":
            return self
        try:
            import torch
            from diffusers import AudioLDM2Pipeline

            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            dtype = torch.float16 if self.device == "cuda" else torch.float32
            self.pipe = AudioLDM2Pipeline.from_pretrained(self.cfg.audioldm_repo, torch_dtype=dtype).to(self.device)
            self.pipe.set_progress_bar_config(disable=True)
        except Exception as e:  # noqa: BLE001
            self.log(f"[SONIDO] AudioLDM2 no disponible ({e}); se usará síntesis procedural.")
            self.pipe = None
        return self

    def unload(self):
        self.pipe = None
        gc.collect()
        try:
            import torch

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except ImportError:
            pass

    def generate(self, sound_type: str, sound_prompt: str, seconds: float, out_path, seed: int | None = None) -> dict:
        """Genera el ambiente de una escena y lo guarda como WAV. Devuelve backend usado y duración."""
        seed = self.cfg.seed if seed is None else seed
        backend = "procedural"
        audio, sr = None, None
        if self.pipe is not None:
            try:
                import torch

                out = self.pipe(
                    sound_prompt,
                    negative_prompt="low quality, noise, music, speech, voice",
                    num_inference_steps=self.cfg.audioldm_steps,
                    audio_length_in_s=self.cfg.audioldm_seconds,
                    generator=torch.Generator("cpu").manual_seed(int(seed)),
                ).audios[0]
                audio = np.asarray(out, dtype=np.float32)
                sr = 16000
                audio = procedural_audio.make_loop(audio, sr, 0.8)
                peak = float(np.max(np.abs(audio))) or 1.0
                audio = audio / peak * 0.8
                backend = "audioldm2"
            except Exception as e:  # noqa: BLE001
                self.log(f"[SONIDO] fallo AudioLDM2 ({e}); se usa síntesis procedural.")
                audio = None
        if audio is None:
            audio, sr = procedural_audio.render(sound_type, seconds, seed)
        write_wav(out_path, audio, sr)
        return {"backend": backend, "seconds": round(len(audio) / sr, 2), "file": Path(out_path).name}
