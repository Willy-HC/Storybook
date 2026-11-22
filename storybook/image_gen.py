"""Generación de ilustraciones con Stable Diffusion 1.5 (+ IP-Adapter opcional) en local."""
from __future__ import annotations

import gc
import time
from pathlib import Path

from .config import ImageConfig
from .schemas import Story


class ImageGenerator:
    def __init__(self, cfg: ImageConfig):
        self.cfg = cfg
        self.pipe = None
        self.device = "cpu"

    # ------------------------------------------------------------------ carga
    def load(self):
        import torch
        from diffusers import DPMSolverMultistepScheduler, StableDiffusionPipeline

        cfg = self.cfg
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        dtype = torch.float16 if self.device == "cuda" else torch.float32
        kwargs = dict(torch_dtype=dtype, safety_checker=None, requires_safety_checker=False)
        try:
            pipe = StableDiffusionPipeline.from_pretrained(cfg.model_id, variant="fp16", **kwargs)
        except (ValueError, OSError):
            pipe = StableDiffusionPipeline.from_pretrained(cfg.model_id, **kwargs)
        pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config, use_karras_sigmas=True)
        if cfg.strategy == "ip_adapter":
            pipe.load_ip_adapter(cfg.ip_adapter_repo, subfolder="models", weight_name=cfg.ip_adapter_weight)
            pipe.set_ip_adapter_scale(cfg.ip_adapter_scale)
        pipe.vae.enable_slicing()
        pipe.set_progress_bar_config(disable=True)
        if self.device == "cuda":
            if cfg.low_vram:
                pipe.enable_model_cpu_offload()
            else:
                pipe.to("cuda")
        self.pipe = pipe
        return self

    def unload(self):
        import torch

        self.pipe = None
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    # ------------------------------------------------------------ generación
    def build_prompt(self, parts: list[str]) -> str:
        """Une fragmentos por prioridad sin exceder los 77 tokens de CLIP (lo que no cabe se omite)."""
        tok = self.pipe.tokenizer
        prompt = ""
        for p in parts:
            p = (p or "").strip().rstrip(".,")
            if not p:
                continue
            cand = f"{prompt}, {p}" if prompt else p
            if len(tok(cand).input_ids) <= 77:
                prompt = cand
        return prompt

    def _call(self, prompt, seed, ip_image, ip_scale):
        import torch
        from PIL import Image

        cfg = self.cfg
        kwargs = dict(
            prompt=prompt,
            negative_prompt=cfg.negative_prompt,
            width=cfg.width,
            height=cfg.height,
            num_inference_steps=cfg.steps,
            guidance_scale=cfg.guidance,
            generator=torch.Generator("cpu").manual_seed(int(seed)),
        )
        if cfg.strategy == "ip_adapter":
            kwargs["ip_adapter_image"] = ip_image or Image.new("RGB", (224, 224), (127, 127, 127))
            self.pipe.set_ip_adapter_scale(ip_scale if ip_image is not None else 0.0)
        return self.pipe(**kwargs).images[0]

    def generate(self, prompt, seed, ip_image=None, ip_scale=None):
        """Genera una imagen; si falta VRAM, activa offload a CPU y reintenta; si falla, cambia la semilla."""
        import torch

        scale = self.cfg.ip_adapter_scale if ip_scale is None else ip_scale
        last = None
        for attempt in range(2):
            try:
                return self._call(prompt, seed + 777 * attempt, ip_image, scale)
            except torch.cuda.OutOfMemoryError as e:
                last = e
                torch.cuda.empty_cache()
                self.pipe.to("cpu")
                self.pipe.enable_model_cpu_offload()
            except Exception as e:  # noqa: BLE001
                last = e
        raise RuntimeError(f"No se pudo generar la imagen: {last}")

    def generate_story_images(self, story: Story, out_dir, progress=None) -> dict:
        """Genera (opcional) la hoja de personaje y las 5 ilustraciones. Devuelve rutas, prompts y tiempos."""
        cfg = self.cfg
        out_dir = Path(out_dir)
        main = story.main_character
        style = story.art_style
        use_ip = cfg.strategy == "ip_adapter"
        sheet_img, sheet_path, sheet_prompt, timings = None, None, None, []

        if use_ip:
            sheet_prompt = self.build_prompt(
                ["character reference sheet, full body portrait, plain light background", main.visual_description, style, cfg.quality_suffix]
            )
            t0 = time.time()
            sheet_img = self.generate(sheet_prompt, cfg.seed)
            timings.append(time.time() - t0)
            sheet_path = out_dir / "character_ref.png"
            sheet_img.save(sheet_path)
            if progress:
                progress(0, len(story.scenes), "Hoja de personaje lista")

        scenes = []
        for i, scene in enumerate(story.scenes, 1):
            present = [c for c in story.characters if c is main or _first(c.name) in scene.text.lower()]
            chars = ", ".join(c.visual_description for c in present[:2])
            # La acción de la escena va PRIMERO (CLIP da más peso a los primeros tokens y recorta el final).
            prompt = self.build_prompt([scene.image_action, chars, story.setting, style, cfg.quality_suffix])
            seed = cfg.seed + i if cfg.vary_seed else cfg.seed
            t0 = time.time()
            img = self.generate(prompt, seed, sheet_img, cfg.ip_adapter_scale if use_ip else None)
            dt = time.time() - t0
            timings.append(dt)
            path = out_dir / f"scene_{i}.png"
            img.save(path)
            scenes.append({"index": i, "file": path.name, "prompt": prompt, "seconds": round(dt, 2), "seed": seed})
            if progress:
                progress(i, len(story.scenes), f"Ilustración {i}/{len(story.scenes)} lista")
        return {
            "scenes": scenes,
            "character_sheet": sheet_path.name if sheet_path else None,
            "character_sheet_prompt": sheet_prompt,
            "total_seconds": round(sum(timings), 2),
        }


def _first(name: str) -> str:
    return name.strip().split()[0].lower() if name.strip() else "\0"
