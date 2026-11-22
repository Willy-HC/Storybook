"""Interfaz Streamlit de Storybook IA.   Ejecutar:  streamlit run app.py"""
from pathlib import Path

import streamlit as st

import storybook  # noqa: F401  (fija variables de entorno antes de importar diffusers)
from storybook.audio_utils import scaled_wav_bytes
from storybook.config import GENRES, IMAGE_MODELS, VOICES, AppConfig
from storybook.pipeline import generate_storybook, list_stories, load_manifest, validate_inputs

st.set_page_config(page_title="Storybook IA", page_icon="📖", layout="wide")
N = 5

st.session_state.setdefault("story_dir", None)
st.session_state.setdefault("scene", 0)


def go(delta: int):
    st.session_state.scene = max(0, min(N - 1, st.session_state.scene + delta))


# ------------------------------------------------------------------ barra lateral
with st.sidebar:
    st.header("⚙️ Configuración")
    strategy = st.radio(
        "Consistencia visual",
        ["ip_adapter", "prompt_only"],
        format_func=lambda s: "IP-Adapter + hoja de personaje" if s == "ip_adapter" else "Solo prompt fijo",
    )
    ip_scale = st.slider("Fuerza IP-Adapter", 0.1, 0.9, 0.35, 0.05, disabled=strategy != "ip_adapter",
                         help="Más alto = personaje más parecido, pero escenas más repetidas.")
    image_model = st.selectbox("Modelo de imagen", list(IMAGE_MODELS), format_func=str)
    sound_backend = st.selectbox("Sonido ambiente", ["procedural", "audioldm2"])
    llm_model = st.text_input("Modelo Ollama", "qwen2.5:7b")
    seed = st.number_input("Semilla de imagen", 0, 99999, 1234)
    st.subheader("🎙️ Voz y volumen")
    voice_name = st.selectbox("Voz de narración", list(VOICES))
    speed = st.slider("Velocidad de la voz", 0.7, 1.3, 0.9, 0.05, help="Menor = más rápida; mayor = más lenta.")
    ambient_gain = st.slider("Volumen del ambiente", 0.1, 1.0, 0.5, 0.05, help="0,5 = la mitad de su volumen.")
    low_vram = st.checkbox("Modo poca VRAM (más lento)", value=False)
    autoplay = st.checkbox("Reproducir audio al cambiar de escena", value=True)

    st.divider()
    st.subheader("📚 Cuentos guardados")
    saved = list_stories()
    if saved:
        pick = st.selectbox("Abrir", saved, format_func=lambda p: p.name)
        if st.button("Abrir cuento"):
            st.session_state.story_dir, st.session_state.scene = str(pick), 0
            st.rerun()
    else:
        st.caption("Aún no hay cuentos generados.")

# ------------------------------------------------------------------ entrada
st.title("📖 Storybook IA")
st.caption("Cuentos ilustrados de 5 escenas con narración y ambientación sonora, generados 100 % en tu equipo.")

with st.form("entrada"):
    idea = st.text_area("💡 Idea de la historia", placeholder="Ej.: Una niña encuentra un zorro de luz que guía a los perdidos")
    c1, c2 = st.columns(2)
    genre_choice = c1.selectbox("🎭 Tipo de cuento", GENRES + ["Otro"])
    custom_genre = c2.text_input("Si elegiste «Otro», escríbelo aquí")
    submitted = st.form_submit_button("✨ Generar cuento")

if submitted:
    genre = custom_genre if genre_choice == "Otro" else genre_choice
    try:
        idea_ok, genre_ok = validate_inputs(idea, genre)
    except ValueError as e:
        st.error(str(e))
    else:
        cfg = AppConfig()
        cfg.image.strategy, cfg.image.ip_adapter_scale = strategy, ip_scale
        cfg.image.seed, cfg.image.low_vram = int(seed), low_vram
        cfg.image.model_id = IMAGE_MODELS[image_model]
        cfg.tts.voice_path, cfg.tts.length_scale = VOICES[voice_name], speed
        cfg.tts.speaker_id = 0 if "Sharvard" in voice_name else None
        cfg.sound.backend, cfg.llm.model = sound_backend, llm_model
        bar = st.progress(0.0, text="Iniciando…")
        try:
            out = generate_storybook(idea_ok, genre_ok, cfg, progress=lambda f, m: bar.progress(min(1.0, f), text=m))
            st.session_state.story_dir, st.session_state.scene = str(out), 0
            st.rerun()
        except Exception as e:  # noqa: BLE001
            bar.empty()
            st.error(f"No se pudo generar el cuento: {e}")

# ------------------------------------------------------------------ visor
if st.session_state.story_dir:
    m = load_manifest(st.session_state.story_dir)
    base = Path(m["dir"])
    i = st.session_state.scene
    sc = m["scenes"][i]

    st.divider()
    st.header(f"«{m['title']}»")
    st.caption(f"Género: {m['genre']}  ·  Escena {i + 1} de {N}: {sc['title']}")
    st.progress((i + 1) / N)

    col_img, col_txt = st.columns([1, 1])
    with col_img:
        st.image(str(base / sc["image"]))
    with col_txt:
        st.markdown(f"### {sc['title']}")
        st.write(sc["text"])
        st.markdown("**🗣️ Narración**")
        st.audio((base / sc["voice"]).read_bytes(), format="audio/wav", autoplay=autoplay)
        st.markdown(f"**🔊 Ambiente** ({sc['sound_type']})")
        st.audio(scaled_wav_bytes(base / sc["ambient"], ambient_gain), format="audio/wav", loop=True, autoplay=autoplay)

    b1, b2, _ = st.columns([1, 1, 6])
    b1.button("⬅ Anterior", on_click=go, args=(-1,), disabled=i == 0)
    b2.button("Siguiente ➡", on_click=go, args=(1,), disabled=i == N - 1)

    with st.expander("🔬 Detalles técnicos y evidencias de consistencia"):
        if m.get("character_sheet"):
            st.image(str(base / m["character_sheet"]), caption="Hoja de personaje (referencia interna para IP-Adapter)", width=256)
        st.write("**Personajes:**", m["characters"])
        st.write("**Prompt de imagen de esta escena:**", sc["image_prompt"])
        st.write("**Tiempos (s):**", m["timings"])
        st.write("**Métricas narrativas:**", m["narrative_metrics"])
        st.write("**Configuración:**", m["config"])
        st.write("**Sistema:**", m["system"])
