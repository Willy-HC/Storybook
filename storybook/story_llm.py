"""Generación del cuento con un LLM local (Ollama) usando salida JSON estructurada."""
from __future__ import annotations

import re

from .config import LLMConfig
from .schemas import SOUND_TYPES, Story, StoryDraft

GENRE_STYLE_HINTS = {
    "terror": "dark moody digital painting, cinematic horror lighting, desaturated colors",
    "fantas": "vibrant fantasy storybook illustration, painterly, magical glowing light",
    "miste": "noir illustration, moody lighting, muted colors, cinematic",
    "aventura": "colorful adventure illustration, dynamic composition, golden hour light",
    "ciencia": "retro-futuristic sci-fi concept art, neon accents, cinematic lighting",
    "infantil": "soft watercolor children's book illustration, pastel colors, friendly shapes",
}


def style_hint(genre: str) -> str:
    g = genre.lower()
    for key, hint in GENRE_STYLE_HINTS.items():
        if key in g:
            return hint
    return "detailed digital storybook illustration, consistent color palette"


SYSTEM_PROMPT = f"""You are a professional fiction writer and storyboard artist.
Write a short illustrated story and return ONLY a JSON object that follows the given schema.

Rules:
- Exactly 5 scenes: scene 1 introduction, scenes 2-4 development with rising conflict, scene 5 resolution.
- Keep the SAME character names, the SAME place and the facts consistent across scenes; each scene must
  continue directly from the previous one.
- The first character in "characters" is the main character and must appear in every scene text.
- "visual_description" is ENGLISH and concrete (age, gender, hair, clothes with colors, one distinctive item).
- "image_action" is ENGLISH, max 20 words, what we SEE in that scene. Do not repeat the character's
  appearance and do not use names there.
- "text" is SPANISH, 55-85 words, third person, past tense, with the tone of the requested genre.
- "sound_type" must be one of: {", ".join(SOUND_TYPES)}.
- "sound_prompt" is ENGLISH, max 12 words, only sounds.
- No explicit sexual content and no graphic gore. If the genre is 'infantil', keep it gentle and child-friendly.
"""


class StoryGenerationError(RuntimeError):
    pass


def _first_token(name: str) -> str:
    return re.split(r"\s+", name.strip())[0].lower()


def check_story(story: Story) -> list[str]:
    """Comprobaciones de coherencia mínimas; devuelve la lista de problemas encontrados."""
    problems = []
    main = _first_token(story.main_character.name)
    mentions = sum(1 for s in story.scenes if main in s.text.lower())
    if mentions < 3:
        problems.append(
            f"The main character '{story.main_character.name}' must appear by name in at least 3 scene texts "
            f"(found {mentions})."
        )
    for i, s in enumerate(story.scenes, 1):
        if len(s.text.split()) < 25:
            problems.append(f"Scene {i} text is too short (min 55 words).")
    return problems


def generate_story(idea: str, genre: str, cfg: LLMConfig, log=print) -> Story:
    try:
        import ollama
    except ImportError as e:  # pragma: no cover
        raise StoryGenerationError("Falta la biblioteca 'ollama' (pip install ollama).") from e

    schema = StoryDraft.model_json_schema()
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"Story idea: {idea}\nGenre: {genre}\nSuggested art style: {style_hint(genre)}\n"
            "Write the story text in Spanish.",
        },
    ]
    last_error = "desconocido"
    for attempt in range(1, cfg.max_retries + 1):
        raw = ""
        try:
            resp = ollama.chat(
                model=cfg.model,
                messages=messages,
                format=schema,
                options={"temperature": cfg.temperature, "num_ctx": cfg.num_ctx},
                keep_alive=0,  # libera la VRAM al terminar para dejarla a Stable Diffusion
            )
            raw = resp.message.content or ""
            draft = StoryDraft.model_validate_json(raw)
            story = Story(**draft.model_dump(), idea=idea, genre=genre)
            problems = check_story(story)
            if problems:
                raise ValueError(" ".join(problems))
            if not story.art_style.strip():
                story.art_style = style_hint(genre)
            return story
        except ValueError as e:  # incluye pydantic.ValidationError
            last_error = str(e)[:400]
            log(f"[LLM] intento {attempt}/{cfg.max_retries} inválido: {last_error}")
            messages += [
                {"role": "assistant", "content": raw},
                {"role": "user", "content": f"That JSON was invalid: {last_error}\nReturn a corrected JSON object only."},
            ]
        except Exception as e:  # conexión, modelo no descargado, etc.
            raise StoryGenerationError(
                f"No se pudo usar Ollama con el modelo '{cfg.model}': {e}\n"
                f"Verifica que Ollama esté abierto y que hayas ejecutado: ollama pull {cfg.model}"
            ) from e
    raise StoryGenerationError(f"El LLM no produjo un cuento válido tras {cfg.max_retries} intentos: {last_error}")
