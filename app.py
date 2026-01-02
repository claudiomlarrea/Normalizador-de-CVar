import streamlit as st

from normalizer import (
    extract_text_from_pdf_bytes,
    normalize_text,
    build_docx_bytes,
    NormalizeOptions,
)

st.set_page_config(page_title="Normalizador de CVar (PDF → TXT limpio)", layout="wide")
st.title("Normalizador de CVar (PDF → TXT limpio)")
st.caption("Entrada: PDF descargado desde CONICET. Salidas: __CVAR_CLEAN.txt y __CVAR_CLEAN.docx (para subir luego al Valorador).")

uploaded = st.file_uploader("Subí el PDF del CVar (CONICET)", type=["pdf"])

if not uploaded:
    st.info("Esperando PDF...")
    st.stop()

pdf_bytes = uploaded.read()

with st.expander("Opciones de normalización", expanded=False):
    remove_personal_data = st.checkbox("Eliminar Datos Personales", value=True)
    remove_rubros_basura = st.checkbox("Eliminar rubros basura (p.ej. 'TECNOLOGÍA E INNOVACIÓN')", value=True)
    remove_nulls = st.checkbox("Eliminar 'null' y variantes", value=True)

opts = NormalizeOptions(
    remove_personal_data=remove_personal_data,
    remove_rubros_basura=remove_rubros_basura,
    remove_nulls=remove_nulls,
)

with st.spinner("Extrayendo texto del PDF y normalizando…"):
    raw_text = extract_text_from_pdf_bytes(pdf_bytes)
    clean_text = normalize_text(raw_text, opts=opts)
    docx_bytes = build_docx_bytes(clean_text)

base_name = uploaded.name.rsplit(".", 1)[0].replace(" ", "_")
txt_name = f"{base_name}__CVAR_CLEAN.txt"
docx_name = f"{base_name}__CVAR_CLEAN.docx"

st.success("Listo: se generó el TXT limpio y el DOCX limpio.")

c1, c2 = st.columns(2)

with c1:
    st.download_button(
        "⬇️ Descargar TXT limpio (__CVAR_CLEAN.txt)",
        data=clean_text.encode("utf-8"),
        file_name=txt_name,
        mime="text/plain; charset=utf-8",
        use_container_width=True,
    )

with c2:
    st.download_button(
        "⬇️ Descargar DOCX limpio (__CVAR_CLEAN.docx)",
        data=docx_bytes,
        file_name=docx_name,
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        use_container_width=True,
    )

st.subheader("Vista previa del TXT limpio")
st.code("\n".join(clean_text.splitlines()[:250]) or "(archivo vacío)", language="text")
