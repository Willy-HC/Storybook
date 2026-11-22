"""Experimentos de consistencia: compara estrategias de generación de imágenes en 3+ historias.

Para cada prueba (idea, género):
  1. Se genera UNA historia con el LLM (la misma para todas las configuraciones).
  2. Se generan las 5 ilustraciones con cada configuración (p. ej. prompt_only vs ip_adapter:0.35).
  3. Se miden tiempos y métricas (CLIP, cobertura de personajes) y se guarda una hoja de contacto.

Uso:
    python experiments/run_experiments.py
    python experiments/run_experiments.py --configs prompt_only,ip_adapter:0.4,ip_adapter:0.7
    python experiments/run_experiments.py --full     # además corre el pipeline completo (voz + sonido)
"""
import argparse
import csv
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import storybook  # noqa: E402,F401
from PIL import Image, ImageDraw  # noqa: E402
from storybook.config import AppConfig  # noqa: E402
from storybook.image_gen import ImageGenerator  # noqa: E402
from storybook.metrics import ClipScorer, narrative_metrics, visual_metrics  # noqa: E402
from storybook.pipeline import generate_storybook, slugify  # noqa: E402
from storybook.story_llm import generate_story  # noqa: E402
from storybook.sysinfo import system_info  # noqa: E402

TESTS = [
    ("Una niña descubre un zorro de luz que guía a los perdidos en un bosque nocturno", "Fantasía"),
    ("Un técnico de mantenimiento oye pasos en una estación espacial que debía estar vacía", "Terror"),
    ("Un detective de pueblo investiga por qué desapareció el reloj de la plaza", "Misterio"),
]
RESULTS = Path(__file__).resolve().parent / "results"


def parse_config(spec: str):
    name, _, scale = spec.partition(":")
    return name, float(scale) if scale else 0.35


def contact_sheet(paths, label, out):
    imgs = [Image.open(p).convert("RGB").resize((256, 256)) for p in paths]
    sheet = Image.new("RGB", (256 * len(imgs), 286), "white")
    ImageDraw.Draw(sheet).text((8, 8), label, fill="black")
    for i, im in enumerate(imgs):
        sheet.paste(im, (256 * i, 30))
    sheet.save(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--configs", default="prompt_only,ip_adapter:0.35")
    ap.add_argument("--tests", type=int, default=len(TESTS))
    ap.add_argument("--full", action="store_true")
    args = ap.parse_args()
    configs = [parse_config(c) for c in args.configs.split(",")]

    RESULTS.mkdir(exist_ok=True)
    scorer = ClipScorer()
    rows = []
    for t_idx, (idea, genre) in enumerate(TESTS[: args.tests], 1):
        tdir = RESULTS / f"prueba{t_idx}_{slugify(genre)}"
        tdir.mkdir(exist_ok=True)
        print(f"\n##### Prueba {t_idx}: {genre} — {idea}")
        story = generate_story(idea, genre, AppConfig().llm)
        (tdir / "story.json").write_text(story.model_dump_json(indent=2), encoding="utf-8")
        nm = narrative_metrics(story)

        for name, scale in configs:
            label = name if name == "prompt_only" else f"{name}_{scale}"
            cdir = tdir / label
            cdir.mkdir(exist_ok=True)
            cfg = AppConfig()
            cfg.image.strategy, cfg.image.ip_adapter_scale = name, scale
            t0 = time.time()
            gen = ImageGenerator(cfg.image).load()
            load_s = time.time() - t0
            try:
                res = gen.generate_story_images(story, cdir)
            finally:
                gen.unload()
            vm = visual_metrics(scorer, cdir, story)
            contact_sheet([cdir / f"scene_{i}.png" for i in range(1, 6)], f"Prueba {t_idx} | {genre} | {label}", cdir / "contact_sheet.png")
            row = {
                "prueba": t_idx, "genero": genre, "config": label,
                "carga_modelo_s": round(load_s, 1), "generacion_5_img_s": res["total_seconds"],
                "personaje_principal_en_escenas": nm["main_character_coverage"], **vm,
            }
            (cdir / "metrics.json").write_text(json.dumps({**row, "prompts": res["scenes"]}, indent=2, ensure_ascii=False), encoding="utf-8")
            rows.append(row)
            print(row)

        if args.full:
            cfg = AppConfig()
            t0 = time.time()
            out = generate_storybook(idea, genre, cfg, out_root=tdir / "pipeline_completo")
            print(f"Pipeline completo -> {out} ({time.time() - t0:.0f} s)")

    with open(RESULTS / "resultados.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    # Resumen por configuración
    lines = ["# Resultados de experimentos\n", "## Sistema\n", "```json", json.dumps(system_info(), indent=2, ensure_ascii=False), "```\n",
             "## Resultados por prueba\n",
             "| Prueba | Género | Config | Carga (s) | 5 img (s) | Pers. en escenas | CLIP pares | CLIP vs esc.1 | CLIP texto |",
             "|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        lines.append(f"| {r['prueba']} | {r['genero']} | {r['config']} | {r['carga_modelo_s']} | {r['generacion_5_img_s']} | "
                     f"{r['personaje_principal_en_escenas']}/5 | {r['clip_pairwise_mean']} | {r['clip_vs_first_mean']} | {r['clip_text_alignment_mean']} |")
    lines += ["\n## Promedio por configuración\n", "| Config | CLIP pares | CLIP vs esc.1 | CLIP texto | 5 img (s) |", "|---|---|---|---|---|"]
    for label in dict.fromkeys(r["config"] for r in rows):
        rs = [r for r in rows if r["config"] == label]
        avg = lambda k: round(sum(r[k] for r in rs) / len(rs), 4)  # noqa: E731
        lines.append(f"| {label} | {avg('clip_pairwise_mean')} | {avg('clip_vs_first_mean')} | {avg('clip_text_alignment_mean')} | {avg('generacion_5_img_s')} |")
    lines += ["\n## Observaciones manuales (COMPLETAR mirando las hojas de contacto)\n",
              "| Prueba | Config | Narrativa | Visual (personaje/estilo) | Fallos detectados | Cambio realizado |", "|---|---|---|---|---|---|"]
    (RESULTS / "REPORTE.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"\nListo. Revisa {RESULTS / 'REPORTE.md'}")


if __name__ == "__main__":
    main()
