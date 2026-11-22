"""Esquemas de datos del cuento (validados con Pydantic).

`StoryDraft` es lo que debe devolver el LLM (se usa como esquema JSON para la salida
estructurada de Ollama). `Story` añade la idea y el género ingresados por el usuario.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from .procedural_audio import SOUND_TYPES

SoundType = Literal[tuple(SOUND_TYPES)]  # type: ignore[valid-type]


class Character(BaseModel):
    name: str = Field(description="Character name (as written in the Spanish text)")
    role: str = Field(description="Role in the story, in Spanish, a few words")
    visual_description: str = Field(
        description="ENGLISH, fixed visual description: age, gender, hair, clothes with colors, "
        "one distinctive item. Max 25 words. Reused verbatim in every image."
    )


class Scene(BaseModel):
    title: str = Field(description="Short scene title in Spanish")
    text: str = Field(description="Narrative text in SPANISH, 55-85 words, third person, past tense")
    image_action: str = Field(
        description="ENGLISH, max 20 words: what is visible (action, framing, lighting). "
        "Do not describe the character's appearance and do not use names."
    )
    sound_type: SoundType = Field(description="Best matching ambient/sound effect category")
    sound_prompt: str = Field(description="ENGLISH, max 12 words, describing only sounds of the scene")


class StoryDraft(BaseModel):
    title: str = Field(description="Story title in Spanish")
    setting: str = Field(description="ENGLISH visual description of the main location, max 20 words")
    art_style: str = Field(description="ENGLISH illustration style keywords, max 15 words")
    characters: list[Character] = Field(min_length=1, max_length=4)
    scenes: list[Scene] = Field(min_length=5, max_length=5)


class Story(StoryDraft):
    idea: str = ""
    genre: str = ""

    @property
    def main_character(self) -> Character:
        return self.characters[0]
