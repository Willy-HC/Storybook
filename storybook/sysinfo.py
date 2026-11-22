"""Información del sistema y versiones de software (para el informe técnico)."""
from __future__ import annotations

import importlib.metadata as md
import platform

LIBS = ["torch", "diffusers", "transformers", "accelerate", "ollama", "piper-tts", "streamlit", "numpy", "pydantic"]


def _ver(pkg):
    try:
        return md.version(pkg)
    except Exception:  # noqa: BLE001
        return None


def system_info() -> dict:
    info = {"python": platform.python_version(), "os": platform.platform(), "cpu": platform.processor()}
    try:
        import psutil

        info["ram_gb"] = round(psutil.virtual_memory().total / 1e9, 1)
        info["cpu_cores"] = psutil.cpu_count(logical=False)
        info["cpu_threads"] = psutil.cpu_count(logical=True)
    except ImportError:
        pass
    try:
        import torch

        info["cuda_available"] = torch.cuda.is_available()
        if torch.cuda.is_available():
            info["gpu"] = torch.cuda.get_device_name(0)
            info["vram_gb"] = round(torch.cuda.get_device_properties(0).total_memory / 1e9, 1)
    except ImportError:
        pass
    info["libs"] = {p: _ver(p) for p in LIBS}
    return info
