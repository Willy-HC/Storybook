"""Pipeline integrador: idea + género -> cuento de 5 escenas con imagen, voz y sonido."""
from __future__ import annotations

import json
import re
import time
import unicodedata
from datetime import datetime
from pathlib import Path

from .audio_utils import wav_duration
from .config import OUTPUTS_DIR, AppConfig
from .image_gen import ImageGenerator
from .metrics import narrative_metrics
from .sound import SoundGenerator
from .story_llm import generate_story
from .sysinfo import system_info
from .tts import Narrator

N_SCENES = 5


def validate_inputs(idea: str, genre: str) -> tuple[str, str]:
    idea, genre = (idea or "").strip(), (genre or "").strip()
    if not idea:
        raise ValueError("La idea de la historia no puede estar vacía.")
    if not genre:
        raise ValueError("Debes indicar el tipo de cuento o historia.")
    return idea, genre


def slugify(text: str, maxlen: int = 40) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()[:maxlen] or "cuento"


def generate_storybook(idea, genre, cfg: AppConfig | None = None, out_root=None, progress=None, log=print) -> Path:
    """Genera un cuento completo y devuelve la carpeta de salida (con manifest.json)."""
    cfg = cfg or AppConfig()
    idea, genre = validate_inputs(idea, genre)
    prog = progress or (lambda frac, msg: None)
    timings: dict[str, float] = {}
    t_start = time.time()

    # 1) Historia ------------------------------------------------------------
    prog(0.02, "Escribiendo la historia con el LLM local…")
    t0 = time.time()
    story = generate_story(idea, genre, cfg.llm, log=log)
    timings["story_s"] = round(time.time() - t0, 1)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = Path(out_root or OUTPUTS_DIR) / f"{stamp}_{slugify(story.title)}"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "story.json").write_text(story.model_dump_json(indent=2), encoding="utf-8")
    prog(0.15, f"Historia lista: «{story.title}». Cargando Stable Diffusion…")

    # 2) Imágenes ------------------------------------------------------------
    t0 = time.time()
    gen = ImageGenerator(cfg.image).load()
    try:
        def img_cb(i, n, msg):
            prog(0.15 + 0.55 * (i / n), msg)

        images = gen.generate_story_images(story, out_dir, img_cb)
    finally:
        gen.unload()
    timings["images_s"] = round(time.time() - t0, 1)

    # 3) Voz -----------------------------------------------------------------
    prog(0.70, "Generando la narración con Piper…")
    t0 = time.time()
    narrator = Narrator(cfg.tts).load()
    voice_secs = []
    for i, scene in enumerate(story.scenes, 1):
        voice_secs.append(narrator.synthesize(scene.text, out_dir / f"scene_{i}_voice.wav"))
        prog(0.70 + 0.15 * (i / N_SCENES), f"Narración {i}/{N_SCENES} lista")
    timings["voice_s"] = round(time.time() - t0, 1)

    # 4) Sonido ambiente -------------------------------------------------------
    prog(0.85, "Generando ambientación sonora…")
    t0 = time.time()
    sg = SoundGenerator(cfg.sound, log=log).load()
    sounds = []
    try:
        for i, scene in enumerate(story.scenes, 1):
            seconds = max(12.0, voice_secs[i - 1] + 3.0)
            sounds.append(sg.generate(scene.sound_type, scene.sound_prompt, seconds, out_dir / f"scene_{i}_ambient.wav", cfg.sound.seed + i))
            prog(0.85 + 0.14 * (i / N_SCENES), f"Ambiente {i}/{N_SCENES} listo")
    finally:
        sg.unload()
    timings["sound_s"] = round(time.time() - t0, 1)
    timings["total_s"] = round(time.time() - t_start, 1)

    # 5) Manifiesto ------------------------------------------------------------
    scenes = []
    for i, scene in enumerate(story.scenes, 1):
        rec = images["scenes"][i - 1]
        scenes.append({
            "index": i,
            "title": scene.title,
            "text": scene.text,
            "image": rec["file"],
            "voice": f"scene_{i}_voice.wav",
            "ambient": f"scene_{i}_ambient.wav",
            "sound_type": scene.sound_type,
            "sound_prompt": scene.sound_prompt,
            "sound_backend": sounds[i - 1]["backend"],
            "image_prompt": rec["prompt"],
            "image_seconds": rec["seconds"],
            "voice_seconds": round(voice_secs[i - 1], 2),
        })
    manifest = {
        "title": story.title,
        "idea": idea,
        "genre": genre,
        "created": stamp,
        "character_sheet": images["character_sheet"],
        "character_sheet_prompt": images["character_sheet_prompt"],
        "characters": [c.model_dump() for c in story.characters],
        "setting": story.setting,
        "art_style": story.art_style,
        "scenes": scenes,
        "timings": timings,
        "narrative_metrics": narrative_metrics(story),
        "config": cfg.to_dict(),
        "system": system_info(),
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    prog(1.0, f"¡Cuento listo en {timings['total_s']} s!")
    return out_dir


def load_manifest(story_dir) -> dict:
    story_dir = Path(story_dir)
    m = json.loads((story_dir / "manifest.json").read_text(encoding="utf-8"))
    m["dir"] = str(story_dir)
    return m


def list_stories(root=None) -> list[Path]:
    root = Path(root or OUTPUTS_DIR)
    if not root.exists():
        return []
    return sorted((p.parent for p in root.glob("*/manifest.json")), reverse=True)


__all__ = ["generate_storybook", "load_manifest", "list_stories", "validate_inputs", "wav_duration"]
