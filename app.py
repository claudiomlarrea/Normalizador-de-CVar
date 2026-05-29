import base64
import json
from pathlib import Path
from typing import Optional

import streamlit as st

from normalizer import (
    extract_text_from_pdf_bytes,
    normalize_text,
    build_docx_bytes,
    build_structured_output,
    extract_sections,
    parse_formacion_academica,
    NormalizeOptions,
)

_APP_DIR = Path(__file__).resolve().parent

# Mismo PNG en `assets/` (opcional). Fallback: escudo servido desde otro repo institucional.
_ESCUDO_REMOTE_URL = (
    "https://raw.githubusercontent.com/claudiomlarrea/valorador_informes_finales/"
    "main/assets/escudo_uccuyo.png"
)


def _resolve_escudo_path() -> Optional[Path]:
    assets = _APP_DIR / "assets"
    if not assets.is_dir():
        return None
    for name in ("escudo_uccuyo.png", "escudo_uccuyo.jpg", "escudo_uccuyo.jpeg"):
        p = assets / name
        if p.is_file():
            return p
    return None


def _escudo_src_for_banner() -> str:
    p = _resolve_escudo_path()
    if p is not None:
        ext = p.suffix.lower()
        mime = "image/jpeg" if ext in (".jpg", ".jpeg") else "image/png"
        b64 = base64.standard_b64encode(p.read_bytes()).decode("ascii")
        return f"data:{mime};base64,{b64}"
    return _ESCUDO_REMOTE_URL


_UCCI_GLOBAL_CSS = """
<style>
:root {
    --ucc-green: #00664d;
    --ucc-green-dark: #00523e;
    --ucc-accent: #28a745;
    --ucc-page-bg: #E6E6E6;
    --ucc-sidebar-bg: #262730;
    --ucc-text: #262730;
    --ucc-heading-card: #2c3838;
    --ucc-lead-muted: #5f6b6f;
}

.stApp {
    background-color: var(--ucc-page-bg);
}

header[data-testid="stHeader"] {
    background: var(--ucc-page-bg) !important;
    border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}
div[data-testid="stDecoration"] {
    height: 3px !important;
    margin-top: env(safe-area-inset-top, 0);
    background: linear-gradient(
        90deg,
        var(--ucc-green-dark) 0%,
        var(--ucc-green) 50%,
        var(--ucc-green-dark) 100%
    ) !important;
}

.block-container {
    padding-top: 2rem !important;
    padding-left: calc(1rem + env(safe-area-inset-left, 0px)) !important;
    padding-right: calc(1rem + env(safe-area-inset-right, 0px)) !important;
}

section[data-testid="stSidebar"] {
    background-color: var(--ucc-sidebar-bg);
}
[data-testid="stSidebar"] [data-testid="stMarkdown"],
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] label {
    color: rgba(255, 255, 255, 0.92);
}

.ucc-inst-header {
    background: var(--ucc-green);
    border-radius: 14px;
    padding: 1.25rem 1.65rem;
    margin-bottom: 1.35rem;
    display: flex;
    flex-direction: row;
    align-items: center;
    gap: 1.35rem;
    flex-wrap: wrap;
    box-sizing: border-box;
}
.ucc-inst-escudo {
    width: 112px;
    max-width: 28vw;
    height: auto;
    flex-shrink: 0;
    display: block;
    object-fit: contain;
    border-radius: 8px;
    background: rgba(255, 255, 255, 0.1);
}
.ucc-inst-banner-text {
    flex: 1 1 240px;
    min-width: 0;
    display: flex;
    flex-direction: column;
    justify-content: center;
}
.header-uccuyo h1.ucc-banner-heading,
.header-uccuyo h2.ucc-banner-heading,
.header-uccuyo h3.ucc-banner-heading {
    color: #ffffff !important;
    margin: 0;
    line-height: 1.2;
    font-family: "Source Sans Pro", ui-sans-serif, system-ui, sans-serif;
}
.header-uccuyo h1.ucc-banner-heading {
    font-size: clamp(1.35rem, 2.8vw, 1.95rem);
    font-weight: 700;
}
.header-uccuyo h2.ucc-banner-heading {
    margin-top: 0.55rem !important;
    font-size: clamp(1rem, 2vw, 1.25rem);
    font-weight: 500;
}
.header-uccuyo h3.ucc-banner-heading {
    margin-top: 0.35rem !important;
    font-size: clamp(0.85rem, 1.4vw, 1rem);
    font-weight: 400;
    color: rgba(255, 255, 255, 0.92) !important;
}

h1:not(.ucc-banner-heading):not(.uc-card-main-title),
h2:not(.ucc-banner-heading),
h3:not(.ucc-banner-heading),
h4 {
    color: var(--ucc-green-dark) !important;
}

.ucc-intro-card {
    background: #ffffff;
    border-radius: 14px;
    padding: 1.75rem 2rem;
    margin-bottom: 1.65rem;
    box-shadow:
        0 8px 28px rgba(0, 0, 0, 0.07),
        0 1px 3px rgba(0, 0, 0, 0.04);
}
.ucc-intro-card h1.uc-card-main-title {
    color: var(--ucc-heading-card) !important;
    margin: 0 0 0.75rem 0 !important;
    font-size: clamp(1.3rem, 2.8vw, 1.85rem);
    font-weight: 700;
    line-height: 1.25;
    font-family: "Source Sans Pro", ui-sans-serif, system-ui, sans-serif;
}
.ucc-intro-card p.uc-card-lead {
    color: var(--ucc-lead-muted) !important;
    margin: 0 !important;
    line-height: 1.6;
    font-size: 1.02rem;
}

p:not(.ucc-banner-heading):not(.uc-card-lead),
label {
    color: var(--ucc-text) !important;
}

[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input,
[data-testid="stTextArea"] textarea {
    border-radius: 12px !important;
    border: 1px solid rgba(0, 82, 62, 0.22) !important;
    background-color: #ffffff !important;
    color: var(--ucc-text) !important;
    caret-color: var(--ucc-green-dark) !important;
}
[data-baseweb="select"] > div:first-child {
    border-radius: 12px !important;
}

[data-testid="stFileUploader"] {
    background-color: transparent !important;
    border: none !important;
    padding: 0 !important;
}
[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] {
    background-color: #1e1e1e !important;
    border-radius: 12px !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    padding: 0.85rem 1rem !important;
}
[data-testid="stFileUploaderDropzone"] label,
[data-testid="stFileUploaderDropzone"] span,
[data-testid="stFileUploaderDropzone"] p,
[data-testid="stFileUploaderDropzone"] small,
[data-testid="stFileUploader"] [data-testid="stMarkdownContainer"] p,
[data-testid="stFileUploader"] [data-testid="stMarkdownContainer"] span {
    color: rgba(255, 255, 255, 0.92) !important;
}

[data-testid="stBaseButton-primary"],
[data-testid="stBaseButton-secondary"],
[data-testid="stBaseButton-tertiary"] {
    background-color: var(--ucc-green) !important;
    color: #ffffff !important;
    border-color: transparent !important;
    --text-color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    font-weight: 600 !important;
}
[data-testid="stBaseButton-primary"]:hover,
[data-testid="stBaseButton-secondary"]:hover,
[data-testid="stBaseButton-tertiary"]:hover {
    background-color: var(--ucc-green-dark) !important;
    border-color: transparent !important;
    color: #ffffff !important;
    --text-color: #ffffff !important;
}
[data-testid="stBaseButton-primary"] p,
[data-testid="stBaseButton-primary"] span,
[data-testid="stBaseButton-secondary"] p,
[data-testid="stBaseButton-secondary"] span,
[data-testid="stBaseButton-tertiary"] p,
[data-testid="stBaseButton-tertiary"] span,
[data-testid="stBaseButton-primary"] div,
[data-testid="stBaseButton-secondary"] div,
[data-testid="stBaseButton-tertiary"] div {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
}
[data-testid="stBaseButton-primary"] svg,
[data-testid="stBaseButton-secondary"] svg,
[data-testid="stBaseButton-tertiary"] svg,
[data-testid="stFileUploader"] button svg {
    fill: #ffffff !important;
    color: #ffffff !important;
}

.stButton > button,
[data-testid="stDownloadButton"] button,
[data-testid="stFileUploader"] button {
    background-color: var(--ucc-green) !important;
    color: #ffffff !important;
    border-radius: 8px !important;
    border: none !important;
    font-weight: 600 !important;
    --text-color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
}
.stButton > button:hover,
[data-testid="stDownloadButton"] button:hover,
[data-testid="stFileUploader"] button:hover {
    background-color: var(--ucc-green-dark) !important;
    border-color: transparent !important;
}
.stButton > button *,
[data-testid="stDownloadButton"] button *,
[data-testid="stFileUploader"] button * {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
}

div[data-testid="stAlert"] {
    border-radius: 10px;
}

.stSlider label,
[data-testid="stTextInput"] label,
[data-testid="stTextArea"] label,
[data-testid="stFileUploader"] label {
    position: relative;
    padding-left: 1rem;
}
.stSlider label::before,
[data-testid="stTextInput"] label::before,
[data-testid="stTextArea"] label::before,
[data-testid="stFileUploader"] label::before {
    content: "";
    position: absolute;
    left: 0;
    top: 0.45rem;
    width: 9px;
    height: 9px;
    border-radius: 50%;
    background: var(--ucc-accent);
}
</style>
"""

st.set_page_config(page_title="Normalizador de CVar (PDF → estructurado)", layout="wide")

st.markdown(_UCCI_GLOBAL_CSS, unsafe_allow_html=True)

_inst_header_html = f"""
<div class="ucc-inst-header header-uccuyo">
<img class="ucc-inst-escudo" src="{_escudo_src_for_banner()}" alt="Universidad Católica de Cuyo" />
<div class="ucc-inst-banner-text">
<h1 class="ucc-banner-heading">Universidad Católica de Cuyo</h1>
<h2 class="ucc-banner-heading">Secretaría de Investigación</h2>
<h3 class="ucc-banner-heading">Consejo de Investigación</h3>
</div>
</div>
"""
st.markdown(_inst_header_html, unsafe_allow_html=True)

st.markdown(
    """
<div class="ucc-intro-card">
<h1 class="uc-card-main-title">Normalizador de CVar (PDF → estructurado)</h1>
<p class="uc-card-lead">Entrada: PDF descargado desde CONICET. Salidas: __CVAR_CLEAN.txt + __CVAR_CLEAN.docx
(estructurado por secciones) + opcional __CVAR_STRUCTURED.json (para puntuar sin regex infinitas).</p>
</div>
""",
    unsafe_allow_html=True,
)

uploaded = st.file_uploader("Subí el PDF del CVar (CONICET)", type=["pdf"])

if not uploaded:
    st.info("Esperando PDF...")
    st.stop()

pdf_bytes = uploaded.read()

with st.expander("Opciones de normalización", expanded=False):
    remove_personal_data = st.checkbox("Eliminar Datos Personales", value=True)
    remove_rubros_basura = st.checkbox(
        "Eliminar rubros basura (p.ej. 'TECNOLOGÍA E INNOVACIÓN')", value=True
    )
    remove_nulls = st.checkbox("Eliminar 'null' y variantes", value=True)
    collapse_spaces = st.checkbox("Normalizar espacios (recomendado)", value=True)

    export_json = st.checkbox("Exportar JSON estructurado (__CVAR_STRUCTURED.json)", value=True)

opts = NormalizeOptions(
    remove_personal_data=remove_personal_data,
    remove_rubros_basura=remove_rubros_basura,
    remove_nulls=remove_nulls,
    collapse_spaces=collapse_spaces,
)

with st.spinner("Extrayendo texto del PDF y normalizando…"):
    raw_text = extract_text_from_pdf_bytes(pdf_bytes)
    clean_text = normalize_text(raw_text, opts=opts)

    # Nueva estrategia: secciones + parse de Formación
    sections = extract_sections(clean_text)
    parsed_formacion = None
    if "FORMACIÓN ACADÉMICA" in sections:
        parsed_formacion = parse_formacion_academica(
            sections.get("FORMACIÓN ACADÉMICA", "")
        )

    # DOCX estructurado
    docx_bytes = build_docx_bytes(
        clean_text=clean_text,
        sections=sections,
        parsed_formacion=parsed_formacion,
    )

    structured = None
    if export_json:
        structured = build_structured_output(clean_text)

base_name = uploaded.name.rsplit(".", 1)[0].replace(" ", "_")
txt_name = f"{base_name}__CVAR_CLEAN.txt"
docx_name = f"{base_name}__CVAR_CLEAN.docx"
json_name = f"{base_name}__CVAR_STRUCTURED.json"

st.success(
    "Listo: se generó el TXT limpio y el DOCX estructurado."
    + (" También el JSON estructurado." if export_json else "")
)

# -------------------------
# Descargas
# -------------------------
c1, c2, c3 = st.columns(3)

with c1:
    st.download_button(
        "⬇️ Descargar TXT limpio (__CVAR_CLEAN.txt)",
        data=clean_text.encode("utf-8"),
        file_name=txt_name,
        mime="text/plain; charset=utf-8",
        type="primary",
        use_container_width=True,
    )

with c2:
    st.download_button(
        "⬇️ Descargar DOCX estructurado (__CVAR_CLEAN.docx)",
        data=docx_bytes,
        file_name=docx_name,
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        type="primary",
        use_container_width=True,
    )

with c3:
    if export_json and structured is not None:
        st.download_button(
            "⬇️ Descargar JSON estructurado (__CVAR_STRUCTURED.json)",
            data=json.dumps(structured, ensure_ascii=False, indent=2).encode("utf-8"),
            file_name=json_name,
            mime="application/json; charset=utf-8",
            type="primary",
            use_container_width=True,
        )
    else:
        st.info("JSON desactivado")

# -------------------------
# Resumen rápido
# -------------------------
st.markdown("---")
st.subheader("Resumen de secciones detectadas")

sec_names = list(sections.keys())
st.write(f"Secciones detectadas: **{len(sec_names)}**")
st.write(", ".join(sec_names) if sec_names else "(ninguna)")

# Si hay formación, mostrar conteo útil para diagnosticar
if parsed_formacion:
    st.subheader("Resumen de Formación académica (diagnóstico)")
    counts = {k: len(v) for k, v in parsed_formacion.items() if v}
    if counts:
        st.json(counts)
    else:
        st.info(
            "Se encontró el bloque de Formación académica, pero no se pudieron separar "
            "entradas (revisar formato del PDF)."
        )

# -------------------------
# Vista previa (por secciones)
# -------------------------
st.markdown("---")
st.subheader("Vista previa")

tab1, tab2, tab3 = st.tabs(
    ["TXT limpio (primeras líneas)", "Secciones (vista)", "Formación académica (detalle)"]
)

with tab1:
    st.code("\n".join(clean_text.splitlines()[:250]) or "(archivo vacío)", language="text")

with tab2:
    if not sections:
        st.info("No se detectaron secciones.")
    else:
        chosen = st.selectbox(
            "Elegí una sección para ver el bloque:", options=sec_names, index=0
        )
        block = sections.get(chosen, "")
        st.code("\n".join(block.splitlines()[:400]) or "(bloque vacío)", language="text")

with tab3:
    if not parsed_formacion:
        st.info("No se detectó / no se pudo parsear Formación académica.")
    else:
        tipo = st.selectbox(
            "Tipo dentro de Formación:",
            options=[
                k
                for k in [
                    "DOCTORADO",
                    "MAESTRÍA",
                    "ESPECIALIZACIÓN",
                    "GRADO",
                    "PROFESORADO",
                    "DIPLOMATURA",
                    "ESTANCIA",
                    "OTRO",
                ]
            ],
            index=0,
        )
        items = parsed_formacion.get(tipo, [])
        st.write(f"Entradas: **{len(items)}**")
        for i, it in enumerate(items[:30], start=1):
            titulo = it.get("titulo", "").strip()
            fin = "FINALIZADO" if it.get("finalizado") else "NO FINALIZADO / EN CURSO"
            st.markdown(f"**{i}. {titulo}** — {fin}")
            st.code((it.get("texto") or "").strip()[:2000], language="text")
