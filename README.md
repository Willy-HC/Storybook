# 📖 Storybook IA — cuentos ilustrados con voz y ambientación sonora (100 % local)

Proyecto Integrador de IA Generativa · Universidad Santo Tomás, Seccional Tunja.

A partir de **solo dos entradas** (idea + tipo de cuento) la aplicación genera un título y **exactamente cinco escenas**.
Cada escena tiene texto, ilustración original, narración con voz sintética y sonido ambiente. Todo corre en tu equipo,
sin APIs de pago: funciona sin Internet una vez descargados los modelos.

| Componente | Tecnología local | Licencia (verificar, ver `docs/LICENCIAS.md`) |
|---|---|---|
| Historia (LLM) | Ollama + Qwen2.5 7B, salida JSON estructurada | Apache-2.0 |
| Imágenes | Stable Diffusion 1.5 (`diffusers`) + IP-Adapter | CreativeML OpenRAIL-M / Apache-2.0 |
| Voz | Piper TTS (voz española) | ver tarjeta de la voz |
| Sonido | Síntesis procedural propia (NumPy) · opcional AudioLDM2 | código propio MIT / AudioLDM2 no comercial |
| Interfaz | Streamlit | Apache-2.0 |
| Métricas | CLIP ViT-B/32 | MIT |

## Cómo se conserva la consistencia

1. **Narrativa:** el LLM produce en una sola llamada un *story bible* (personajes con descripción visual fija, escenario, estilo)
   y las 5 escenas; se valida con Pydantic (exactamente 5 escenas) y con una comprobación de que el protagonista aparece por nombre.
   Si falla, se reintenta enviando el error al modelo.
2. **Visual:** la descripción del personaje, el escenario y el estilo se copian **literalmente** en el prompt de las 5 imágenes,
   con la misma semilla. Con la estrategia `ip_adapter` además se genera una *hoja de personaje* interna (un retrato de referencia,
   no cuenta como escena) que condiciona cada escena mediante IP-Adapter.
3. **Audio:** la narración es el texto exacto de cada escena; el ambiente lo elige el LLM entre 18 categorías (lluvia, fuego, cueva, …).

## Requisitos

* Windows 10/11, Linux o macOS · Python **3.10–3.12** · Git
* GPU NVIDIA con ≥ 6 GB de VRAM recomendada (probado en el diseño para RTX 3050 6 GB) y 16 GB+ de RAM.
  Sin GPU funciona por CPU, pero muy lento.
* ~20 GB libres en disco (≈ 28 GB si descargas AudioLDM2).
* [Ollama](https://ollama.com/download) instalado.

## Instalación paso a paso (Windows / PowerShell)

```powershell
# 1. Clonar
git clone https://github.com/<tu-usuario>/storybook-ia.git
cd storybook-ia

# 2. Entorno virtual
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. PyTorch con CUDA (ANTES del resto)
pip install torch --index-url https://download.pytorch.org/whl/cu124

# 4. Dependencias
pip install -r requirements.txt
pip freeze > requirements.lock.txt      # congela las versiones exactas que te funcionaron (para reproducibilidad)

# 5. Modelos (requiere Internet SOLO esta vez). Ollama debe estar abierto.
python scripts/download_models.py        # añade --audioldm si quieres el modelo de sonido generativo

# 6. Verificar el entorno
python scripts/check_env.py
```

Los pesos de Hugging Face quedan en `models/hf/` (excluidos de Git) y el LLM en la carpeta de Ollama.

En Linux/macOS usa `source .venv/bin/activate` en lugar del paso 2 de activación.

## Ejecución

```powershell
streamlit run app.py
```

Escribe una idea, elige el género y pulsa **Generar cuento**. Navega con *Anterior / Siguiente*; cada escena tiene dos reproductores
independientes (narración y ambiente, este último en bucle). La barra lateral permite cambiar estrategia de consistencia, modelo, semilla
y abrir cuentos ya generados (carpeta `outputs/`).

Desde la terminal: `python cli.py --idea "Una niña encuentra un zorro de luz" --genre "Fantasía"`

### Ejemplo de uso

* Idea: *Una niña descubre un zorro de luz que guía a los perdidos en un bosque nocturno*
* Tipo: *Fantasía*
* Resultado en `outputs/<fecha>_<título>/`: `scene_1.png … scene_5.png`, `scene_N_voice.wav`, `scene_N_ambient.wav`,
  `character_ref.png`, `story.json` y `manifest.json` (prompts, tiempos, configuración y versiones).

### Probar sin Internet

```powershell
$env:STORYBOOK_OFFLINE = 1
streamlit run app.py
```

## Experimentos y evidencias

```powershell
python experiments/run_experiments.py                                   # 3 pruebas × (prompt_only vs ip_adapter:0.6)
python experiments/run_experiments.py --configs prompt_only,ip_adapter:0.4,ip_adapter:0.7
python experiments/run_experiments.py --full                            # además guarda cuentos completos con voz y sonido
```

Genera en `experiments/results/`: hojas de contacto con las 5 escenas por prueba y configuración, `resultados.csv` y `REPORTE.md`
(tiempos, similitud CLIP entre escenas, cobertura del protagonista). Completa en ese reporte las observaciones manuales.

Pruebas automáticas: `pytest -q`

## Estructura

```
app.py                  Interfaz Streamlit
cli.py                  Generación desde terminal
storybook/
  config.py             Parámetros y rutas (modelos, semilla, estrategia…)
  schemas.py            Esquemas Pydantic (5 escenas obligatorias)
  story_llm.py          Historia con Ollama (JSON estructurado + reintentos)
  image_gen.py          Stable Diffusion 1.5 + IP-Adapter, control de tokens y de VRAM
  tts.py                Voz con Piper
  procedural_audio.py   18 ambientes/efectos sintetizados con NumPy
  sound.py              Fachada de sonido (procedural o AudioLDM2 con respaldo)
  metrics.py            Métricas de consistencia (CLIP + cobertura narrativa)
  pipeline.py           Orquestación y manifiesto
  sysinfo.py            Hardware y versiones
scripts/                download_models.py · check_env.py
experiments/            run_experiments.py · results/
tests/                  Pruebas automáticas
docs/                   Arquitectura, informe técnico, licencias, guion del video
```

## Limitaciones conocidas

* SD 1.5 a 512×512 no garantiza identidad exacta del personaje (ropa/rostro pueden variar); IP-Adapter mejora pero no elimina esto.
* Un LLM de 7 B parámetros puede cometer errores gramaticales o de continuidad menores en español.
* La voz Piper es neutra y poco expresiva; el ambiente procedural es sencillo frente a una grabación real.
* Tiempos: ver `manifest.json` y `experiments/results/REPORTE.md` en el equipo de pruebas.

## Ética y derechos

Las imágenes y el audio son sintéticos; revisa las licencias en `docs/LICENCIAS.md`. No se usan voces clonadas ni datos personales.
Stable Diffusion se carga sin *safety checker* para no bloquear falsos positivos en géneros como terror; el prompt del LLM
prohíbe contenido sexual explícito y gore gráfico. Revisa los cuentos antes de mostrarlos a menores.
