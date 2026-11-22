"""Verifica el entorno: hardware, versiones, GPU, Ollama y modelos descargados."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import storybook  # noqa: E402,F401
from storybook.config import AppConfig  # noqa: E402
from storybook.sysinfo import system_info  # noqa: E402

cfg = AppConfig()
print(json.dumps(system_info(), indent=2, ensure_ascii=False))

try:
    import torch

    if not torch.cuda.is_available():
        print("\n[!] CUDA no disponible: la generación de imágenes irá por CPU (muy lenta). Revisa la instalación de PyTorch.")
except ImportError:
    print("\n[!] PyTorch no está instalado.")

try:
    import ollama

    names = [m.model for m in ollama.list().models]
    ok = any(n.startswith(cfg.llm.model) for n in names)
    print(f"\nOllama: {'OK' if ok else 'FALTA'} modelo {cfg.llm.model} (instalados: {names})")
    if not ok:
        print(f"    -> ollama pull {cfg.llm.model}")
except Exception as e:  # noqa: BLE001
    print(f"\n[!] No se pudo contactar con Ollama: {e}\n    -> Abre la aplicación Ollama.")

try:
    from storybook.tts import ensure_voice_files

    ensure_voice_files(cfg.tts)
    print("Voz Piper: OK")
except Exception as e:  # noqa: BLE001
    print(f"[!] Voz Piper no disponible: {e}")
