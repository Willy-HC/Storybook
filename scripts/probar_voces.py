"""Genera la misma frase con cada voz y velocidad para que escuches y elijas.

Uso:   python scripts/probar_voces.py
Salida: outputs/voces/<voz>_vel<velocidad>.wav  (ábrelos con el reproductor de Windows)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import storybook  # noqa: E402,F401
from storybook.config import OUTPUTS_DIR, VOICES, TTSConfig  # noqa: E402
from storybook.tts import Narrator  # noqa: E402

FRASE = ("Luna caminó despacio por el bosque oscuro. De pronto, entre las ramas, "
         "vio un resplandor dorado que la llamaba por su nombre.")
SPEEDS = [0.85, 0.95, 1.05]
out = OUTPUTS_DIR / "voces"
out.mkdir(parents=True, exist_ok=True)

for name, path in VOICES.items():
    try:
        cfg = TTSConfig(voice_path=path, speaker_id=0 if "Sharvard" in name else None)
        narrator = Narrator(cfg).load()
    except Exception as e:  # noqa: BLE001
        print(f"[omitida] {name}: {e}")
        continue
    for sp in SPEEDS:
        narrator.cfg.length_scale = sp
        f = out / f"{Path(path).name}_vel{sp}.wav"
        narrator.synthesize(FRASE, f)
        print("OK", f)
print(f"\nEscucha los archivos en {out}. length_scale menor = más rápido.")
