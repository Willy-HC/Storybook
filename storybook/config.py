"""Configuración central del proyecto (modelos, parámetros y rutas)."""
from __future__ import annotations

import os
from dataclasses import asdict, dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = ROOT / "models"
OUTPUTS_DIR = ROOT / "outputs"

# Todo lo que descargue Hugging Face queda dentro del proyecto (carpeta models/).
os.environ.setdefault("HF_HOME", str(MODELS_DIR / "hf"))
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
# Con STORYBOOK_OFFLINE=1 se impide cualquier acceso a Internet (prueba de ejecución local).
if os.environ.get("STORYBOOK_OFFLINE") == "1":
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"

GENRES = ["Fantasía", "Terror", "Misterio", "Aventura", "Ciencia ficción", "Infantil"]

# Modelos de imagen compatibles con IP-Adapter SD1.5 (ambos ~2 GB en fp16, caben en 6 GB de VRAM).
IMAGE_MODELS = {
    "DreamShaper 8 (recomendado, más calidad)": "Lykon/dreamshaper-8",
    "Stable Diffusion 1.5 base": "stable-diffusion-v1-5/stable-diffusion-v1-5",
}

# Voces Piper en español (ruta dentro de rhasspy/piper-voices). Prueba cuál suena mejor con scripts/probar_voces.py
VOICES = {
    "México · Claude (alta calidad)": "es/es_MX/claude/high/es_MX-claude-high",
    "México · Ald (media)": "es/es_MX/ald/medium/es_MX-ald-medium",
    "España · Sharvard (media)": "es/es_ES/sharvard/medium/es_ES-sharvard-medium",
    "España · Davefx (media)": "es/es_ES/davefx/medium/es_ES-davefx-medium",
}


@dataclass
class LLMConfig:
    model: str = "qwen2.5:7b"      # alternativa más liviana: "qwen2.5:3b" (licencia distinta, ver docs)
    temperature: float = 0.7
    num_ctx: int = 4096
    max_retries: int = 3


@dataclass
class ImageConfig:
    model_id: str = "Lykon/dreamshaper-8"
    width: int = 512
    height: int = 512
    steps: int = 30
    guidance: float = 7.5
    seed: int = 1234
    negative_prompt: str = (
        "text, watermark, signature, logo, blurry, low quality, deformed, disfigured, "
        "extra limbs, extra fingers, bad anatomy, ugly, duplicate, lowres, jpeg artifacts, cropped, out of frame"
    )
    quality_suffix: str = "masterpiece, best quality, highly detailed, sharp focus"
    vary_seed: bool = True          # semilla distinta por escena (misma semilla => composiciones casi idénticas)
    # Estrategia de consistencia visual:
    #   "prompt_only": descripción fija del personaje + estilo + misma semilla
    #   "ip_adapter" : lo anterior + hoja de personaje como referencia vía IP-Adapter
    strategy: str = "ip_adapter"
    ip_adapter_repo: str = "h94/IP-Adapter"
    ip_adapter_weight: str = "ip-adapter_sd15.bin"
    ip_adapter_scale: float = 0.35  # alto (>0.6) copia la referencia y las 5 escenas salen casi iguales
    low_vram: bool = False          # True = offload a CPU (más lento, menos VRAM)


@dataclass
class TTSConfig:
    voice_repo: str = "rhasspy/piper-voices"
    voice_path: str = "es/es_MX/claude/high/es_MX-claude-high"
    length_scale: float = 0.9       # <1 = más rápido, >1 = más lento (1.0 = velocidad original del modelo)
    noise_scale: float = 0.667
    noise_w_scale: float = 0.8
    speaker_id: int | None = None   # solo voces multihablante (p. ej. Sharvard: 0 o 1)


@dataclass
class SoundConfig:
    backend: str = "procedural"     # "procedural" (rápido, sin descargas) | "audioldm2" (modelo generativo)
    audioldm_repo: str = "cvssp/audioldm2"
    audioldm_steps: int = 50
    audioldm_seconds: float = 10.0
    seed: int = 7
    ambient_gain: float = 0.5       # volumen de reproducción del ambiente respecto a su nivel base


@dataclass
class AppConfig:
    llm: LLMConfig = field(default_factory=LLMConfig)
    image: ImageConfig = field(default_factory=ImageConfig)
    tts: TTSConfig = field(default_factory=TTSConfig)
    sound: SoundConfig = field(default_factory=SoundConfig)

    def to_dict(self) -> dict:
        return asdict(self)
