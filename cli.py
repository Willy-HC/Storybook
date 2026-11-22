"""Genera un cuento desde la terminal.

Ejemplo:
    python cli.py --idea "Una niña encuentra un zorro de luz en el bosque" --genre "Fantasía"
"""
import argparse

import storybook  # noqa: F401  (fija variables de entorno antes de importar diffusers)
from storybook.config import AppConfig
from storybook.pipeline import generate_storybook


def main():
    ap = argparse.ArgumentParser(description="Storybook IA local")
    ap.add_argument("--idea", required=True)
    ap.add_argument("--genre", required=True)
    ap.add_argument("--strategy", choices=["prompt_only", "ip_adapter"], default="ip_adapter")
    ap.add_argument("--ip-scale", type=float, default=0.6)
    ap.add_argument("--sound-backend", choices=["procedural", "audioldm2"], default="procedural")
    ap.add_argument("--llm-model", default=None)
    ap.add_argument("--seed", type=int, default=1234)
    ap.add_argument("--low-vram", action="store_true")
    a = ap.parse_args()

    cfg = AppConfig()
    cfg.image.strategy, cfg.image.ip_adapter_scale = a.strategy, a.ip_scale
    cfg.image.seed, cfg.image.low_vram = a.seed, a.low_vram
    cfg.sound.backend = a.sound_backend
    if a.llm_model:
        cfg.llm.model = a.llm_model

    out = generate_storybook(a.idea, a.genre, cfg, progress=lambda f, m: print(f"[{f:4.0%}] {m}"))
    print(f"\nCuento guardado en: {out}")


if __name__ == "__main__":
    main()
