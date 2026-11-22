"""Pruebas básicas (no requieren GPU, Ollama ni modelos):  pytest -q"""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from storybook import procedural_audio as pa  # noqa: E402
from storybook.audio_utils import wav_duration, write_wav  # noqa: E402
from storybook.pipeline import slugify, validate_inputs  # noqa: E402
from storybook.schemas import Story  # noqa: E402


def _scene(i):
    return dict(title=f"Escena {i}", text="Luna caminó por el bosque " * 12, image_action="walking in forest",
                sound_type="forest", sound_prompt="birds and wind")


def _story_dict(n_scenes=5):
    return dict(title="T", setting="forest", art_style="watercolor",
                characters=[dict(name="Luna", role="niña", visual_description="girl, red hair")],
                scenes=[_scene(i) for i in range(n_scenes)])


def test_validate_inputs_rechaza_vacios():
    with pytest.raises(ValueError):
        validate_inputs("   ", "Terror")
    with pytest.raises(ValueError):
        validate_inputs("idea", "")
    assert validate_inputs(" idea ", " Terror ") == ("idea", "Terror")


def test_story_exige_cinco_escenas():
    assert len(Story(**_story_dict(5)).scenes) == 5
    for n in (4, 6):
        with pytest.raises(ValueError):
            Story(**_story_dict(n))


def test_story_rechaza_sonido_desconocido():
    d = _story_dict()
    d["scenes"][0]["sound_type"] = "no_existe"
    with pytest.raises(ValueError):
        Story(**d)


@pytest.mark.parametrize("kind", pa.SOUND_TYPES)
def test_sonidos_procedurales(kind, tmp_path):
    x, sr = pa.render(kind, 8, seed=3)
    assert np.isfinite(x).all() and 0.1 < np.abs(x).max() <= 0.81
    p = write_wav(tmp_path / f"{kind}.wav", x, sr)
    assert abs(wav_duration(p) - len(x) / sr) < 0.01


def test_slugify():
    assert slugify("¡El Zorro de Luz!") == "el-zorro-de-luz"
