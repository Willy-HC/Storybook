"""Métricas objetivas de consistencia (evidencia para el informe).

* Narrativa: en cuántas escenas aparece cada personaje por nombre.
* Visual: similitud coseno CLIP entre las ilustraciones (proxy de coherencia de estilo/personaje)
  y alineación CLIP texto-imagen con la acción de cada escena.
Son indicadores aproximados: complementan, no reemplazan, la revisión visual manual.
"""
from __future__ import annotations

from pathlib import Path

from .schemas import Story

CLIP_ID = "openai/clip-vit-base-patch32"


def narrative_metrics(story: Story) -> dict:
    cov = {}
    for c in story.characters:
        token = c.name.strip().split()[0].lower() if c.name.strip() else ""
        cov[c.name] = sum(1 for s in story.scenes if token and token in s.text.lower())
    words = [len(s.text.split()) for s in story.scenes]
    return {
        "scenes": len(story.scenes),
        "character_scene_coverage": cov,
        "main_character_coverage": cov.get(story.main_character.name, 0),
        "words_per_scene": words,
    }


class ClipScorer:
    def __init__(self):
        import torch
        from transformers import CLIPModel, CLIPProcessor

        self.torch = torch
        self.model = CLIPModel.from_pretrained(CLIP_ID).eval()
        self.proc = CLIPProcessor.from_pretrained(CLIP_ID)

    def _img_emb(self, paths):
        from PIL import Image

        imgs = [Image.open(p).convert("RGB") for p in paths]
        with self.torch.no_grad():
            e = self.model.get_image_features(**self.proc(images=imgs, return_tensors="pt"))
        return e / e.norm(dim=-1, keepdim=True)

    def _txt_emb(self, texts):
        with self.torch.no_grad():
            e = self.model.get_text_features(**self.proc(text=texts, return_tensors="pt", padding=True, truncation=True))
        return e / e.norm(dim=-1, keepdim=True)

    def visual_metrics(self, image_paths, texts) -> dict:
        emb = self._img_emb(image_paths)
        sims = emb @ emb.T
        n = len(image_paths)
        pair = [float(sims[i, j]) for i in range(n) for j in range(i + 1, n)]
        vs_first = [float(sims[0, j]) for j in range(1, n)]
        txt = self._txt_emb(texts)
        align = [float((emb[i] * txt[i]).sum()) for i in range(n)]
        return {
            "clip_pairwise_mean": round(sum(pair) / len(pair), 4),
            "clip_vs_first_mean": round(sum(vs_first) / len(vs_first), 4),
            "clip_text_alignment_mean": round(sum(align) / len(align), 4),
        }


def visual_metrics(scorer: ClipScorer, out_dir, story: Story) -> dict:
    out_dir = Path(out_dir)
    paths = [out_dir / f"scene_{i}.png" for i in range(1, len(story.scenes) + 1)]
    return scorer.visual_metrics(paths, [s.image_action for s in story.scenes])
