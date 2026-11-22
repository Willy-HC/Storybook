# Informe técnico — Storybook IA

**Autor:** [Tu nombre] · **Curso:** Electiva Ingeniería Aplicada — IA Generativa · Universidad Santo Tomás, Tunja · 2026

> Plantilla ya alineada con el enunciado. Reemplaza los textos entre `[CORCHETES]` con tus mediciones y evidencias,
> y exporta a PDF (VS Code → extensión *Markdown PDF*, o Pandoc).

## 1. Problema y objetivo
Generar localmente, a partir de una idea y un tipo de cuento, una historia de cinco escenas con texto, ilustración, narración y ambiente sonoro,
manteniendo la consistencia de personajes, escenario y estilo, sin APIs de pago.

## 2. Arquitectura y flujo de datos
Ver `docs/ARQUITECTURA.md` (insertar el diagrama). Canal único de información: *story bible* JSON validado con Pydantic.

## 3. Tecnologías y justificación
| Componente | Elegido | Justificación | Alternativa descartada |
|---|---|---|---|
| LLM | Qwen2.5 7B vía Ollama | Buen español, JSON estructurado por esquema, cabe en 6 GB con offload parcial, licencia Apache-2.0 | Modelos 3B (menor calidad/licencia distinta) [COMPLETAR] |
| Imagen | SD 1.5 fp16 + IP-Adapter | Cabe cómodamente en 6 GB; IP-Adapter permite condicionar por imagen sin entrenar | SDXL (no cabe sin offload pesado) [COMPLETAR] |
| Voz | Piper | Ligero, CPU, voz española, sin descarga de pesos grandes | XTTS (pesado/licencia) [COMPLETAR] |
| Sonido | Procedural + AudioLDM2 opcional | Instantáneo, sin licencias, 100 % offline | Biblioteca de grabaciones (licencias) |
| UI | Streamlit | Audio nativo, estado de sesión, desarrollo rápido | Gradio/Pygame |

## 4. Procedimiento de generación de las cinco escenas
1) Validación de entradas. 2) LLM → JSON (título, escenario, estilo, personajes, 5 escenas). 3) Hoja de personaje (solo `ip_adapter`).
4) 5 ilustraciones con prompt = estilo + descripción fija + acción + escenario (recortado a 77 tokens por prioridad). 5) Voz por escena.
6) Ambiente por escena (duración ≥ voz + 3 s, bucle sin costura). 7) `manifest.json`.

## 5. Estrategia de consistencia
* **Narrativa:** story bible en una sola llamada, reglas explícitas, verificación de aparición del protagonista, reintentos.
* **Visual:** descripción literal del personaje + estilo + semilla común; IP-Adapter con hoja de personaje (escala configurable).
* **Audio/contenido:** la voz lee el texto exacto; el tipo de sonido proviene del mismo JSON de la escena.

## 6. Configuraciones y experimentos
Configuraciones comparadas: **A = `prompt_only`**, **B = `ip_adapter` (escala 0,35)** [y otras escalas si las probaste].
Misma historia y semilla en ambas, para aislar el efecto de la estrategia.

[PEGAR AQUÍ la tabla de `experiments/results/REPORTE.md`]

**Conclusión y configuración final:** [COMPLETAR: cuál ganó, por qué (métricas CLIP + inspección visual), compromiso entre consistencia y variedad de composición].

## 7. Evidencias de pruebas (≥ 3)
| Prueba | Idea | Género | Evidencia |
|---|---|---|---|
| 1 | [..] | [..] | `experiments/results/prueba1_*/…/contact_sheet.png` |
| 2 | [..] | [..] | … |
| 3 | [..] | [..] | … |

Registro por prueba (dimensiones del enunciado):
| Dimensión | Qué se comprobó | Resultado | Fallos | Cambio realizado |
|---|---|---|---|---|
| Narrativa | personajes, hechos, secuencia | [..] | [..] | [..] |
| Visual | personaje y estilo reconocibles | [..] | [..] | [..] |
| Audio y contenido | voz = texto; ambiente pertinente | [..] | [..] | [..] |
| Funcionamiento | 5 escenas sin errores, navegación y audio | [..] | [..] | [..] |

## 8. Hardware, software y tiempos
* Equipo: Lenovo LOQ 15IAX9 · Intel Core i5-12450HX · 24 GB RAM · NVIDIA RTX 3050 6 GB · Windows 64 bits.
* Versiones: ver `requirements.lock.txt` y el campo `system` de `manifest.json`.
* Tiempos medidos (`manifest.json → timings`): historia [..] s · imágenes [..] s · voz [..] s · sonido [..] s · total [..] s.

## 9. Resultados, limitaciones y trabajo futuro
[COMPLETAR] Ver limitaciones conocidas del README (identidad del personaje, calidad del LLM 7B, voz neutra).

## 10. Consideraciones éticas, licencias y derechos de voz/audio
Ver `docs/LICENCIAS.md`. Contenido sintético; sin voces clonadas; sin datos personales; moderación mediante instrucciones al LLM
(SD sin *safety checker*, decisión documentada); revisión humana recomendada para público infantil.
