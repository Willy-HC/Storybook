"""Descarga todos los modelos necesarios para ejecutar el proyecto sin conexión.

Uso:
    python scripts/download_models.py              # núcleo (LLM, SD1.5, IP-Adapter, voz, CLIP)
    python scripts/download_models.py --audioldm   # además AudioLDM2 (opcional, ~7 GB)
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import storybook  # noqa: E402,F401
from storybook.config import MODELS_DIR, AppConfig  # noqa: E402


def step(msg):
    print(f"\n=== {msg}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--audioldm", action="store_true")
    ap.add_argument("--skip-llm", action="store_true")
    args = ap.parse_args()
    cfg = AppConfig()

    if not args.skip_llm:
        step(f"LLM en Ollama: {cfg.llm.model}")
        try:
            import ollama

            ollama.pull(cfg.llm.model)
            print("OK")
        except Exception as e:  # noqa: BLE001
            print(f"No se pudo descargar con la API ({e}).\nEjecuta manualmente:  ollama pull {cfg.llm.model}")

    step("Stable Diffusion 1.5 + IP-Adapter")
    from storybook.image_gen import ImageGenerator

    cfg.image.strategy = "ip_adapter"
    ImageGenerator(cfg.image).load().unload()
    print("OK")

    step("Voz Piper (español)")
    from storybook.tts import ensure_voice_files

    onnx, _ = ensure_voice_files(cfg.tts)
    print("OK ->", onnx)
    try:
        from huggingface_hub import hf_hub_download

        card = hf_hub_download(cfg.tts.voice_repo, str(Path(cfg.tts.voice_path).parent / "MODEL_CARD"))
        dst = MODELS_DIR / "model_cards"
        dst.mkdir(parents=True, exist_ok=True)
        (dst / "piper_voice_MODEL_CARD.txt").write_text(Path(card).read_text(encoding="utf-8"), encoding="utf-8")
        print("Tarjeta de la voz copiada a models/model_cards/ (REVISA su licencia y cítala en docs/LICENCIAS.md)")
    except Exception as e:  # noqa: BLE001
        print("(No se pudo copiar la tarjeta del modelo de voz:", e, ")")

    step("CLIP (métricas de consistencia)")
    from storybook.metrics import CLIP_ID
    from transformers import CLIPModel, CLIPProcessor

    CLIPModel.from_pretrained(CLIP_ID)
    CLIPProcessor.from_pretrained(CLIP_ID)
    print("OK")

    if args.audioldm:
        step("AudioLDM2 (opcional)")
        from diffusers import AudioLDM2Pipeline

        AudioLDM2Pipeline.from_pretrained(cfg.sound.audioldm_repo)
        print("OK")

    print("\nListo. Para probar sin Internet:  set STORYBOOK_OFFLINE=1  (PowerShell: $env:STORYBOOK_OFFLINE=1)")


if __name__ == "__main__":
    main()
