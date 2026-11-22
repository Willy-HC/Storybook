# Modelos, recursos y licencias

> **Verifica cada licencia en su página oficial en la fecha de entrega** y anota aquí la fecha. Lo siguiente es un punto de partida.

| Recurso | Uso | Licencia (a verificar) | Dónde revisar |
|---|---|---|---|
| Código de este repositorio | — | MIT | `LICENSE` |
| Qwen2.5-7B-Instruct (vía Ollama) | Historia | Apache-2.0 (el 3B usa una licencia de investigación distinta) | Tarjeta del modelo en Hugging Face / Ollama |
| Stable Diffusion v1.5 | Imágenes | CreativeML OpenRAIL-M (restricciones de uso) | `stable-diffusion-v1-5/stable-diffusion-v1-5` |
| IP-Adapter (`ip-adapter_sd15`) | Consistencia visual | Apache-2.0 | `h94/IP-Adapter` |
| Piper TTS (paquete `piper-tts`) | Voz | MIT en versiones antiguas; las recientes publican bajo GPL-3.0 | Repositorio de Piper / PyPI |
| Voz `es_ES-davefx-medium` | Voz | Ver `MODEL_CARD` (copiada en `models/model_cards/` por `download_models.py`) | `rhasspy/piper-voices` |
| Sonido procedural | Ambientes | Código propio (MIT), sin grabaciones de terceros | `storybook/procedural_audio.py` |
| AudioLDM2 (opcional) | Ambientes generativos | Licencia no comercial (CC BY-NC) | `cvssp/audioldm2` |
| CLIP ViT-B/32 | Métricas | MIT | `openai/clip-vit-base-patch32` |
| Streamlit, diffusers, transformers, etc. | Infraestructura | Apache-2.0 / BSD | PyPI |

## Derechos de voz y audio

* La voz es un modelo sintético preentrenado; **no se clonó ninguna voz real**.
* El ambiente sonoro se genera desde cero; no se redistribuyen grabaciones de terceros.
* Los pesos de modelos no se publican en el repositorio (carpeta `models/` en `.gitignore`).
