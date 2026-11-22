# Guion del video de demostración (≈ 5 min)

1. **(0:00)** Presentación: nombre, curso, objetivo. Muestra la carpeta del proyecto y `python scripts/check_env.py` (hardware y GPU).
2. **(0:30)** Explica la arquitectura con `docs/ARQUITECTURA.md` (LLM → story bible → imagen/voz/sonido → Streamlit).
3. **(1:00)** Abre la app (`streamlit run app.py`). Intenta generar con campos vacíos → muestra la validación.
4. **(1:30)** Escribe idea y género; pulsa *Generar*. Mientras corre, comenta los modelos (Qwen2.5, SD1.5 + IP-Adapter, Piper, sonido procedural).
5. **(3:00)** Recorre las 5 escenas con *Siguiente*: texto, imagen, voz y ambiente (señala que el ambiente se distingue de la voz y se controla aparte).
6. **(4:00)** Abre «Detalles técnicos»: hoja de personaje, prompts, tiempos y métricas.
7. **(4:30)** Muestra `experiments/results/` (hojas de contacto de las 3 pruebas y comparación de configuraciones).
8. **(5:00)** Cierre: limitaciones y modo offline (`STORYBOOK_OFFLINE=1`).
