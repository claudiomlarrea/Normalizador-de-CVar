import streamlit as st

st.set_page_config(page_title="Normalizador de CVar (CONICET)", layout="wide")
st.title("Normalizador de CVar (PDF CONICET → TXT/DOCX)")
st.caption("Subí un PDF CVar y descargá TXT/DOCX limpios.")

uploaded = st.file_uploader("Subí el PDF CVar descargado de CONICET", type=["pdf"])

if uploaded is None:
    st.info("Esperando que subas un PDF...")
    st.stop()

# Imports pesados SOLO después de subir PDF
from normalizer import NormalizeOptions, extract_text_from_pdf_bytes, normalize_text, build_docx_bytes

remove_personal = st.checkbox("Eliminar DATOS PERSONALES (recomendado)", value=True)
remove_rubros = st.checkbox("Eliminar rótulos basura (TECNOLOGÍA E INNOVACIÓN)", value=True)
remove_nulls = st.checkbox("Eliminar null / null(ed)", value=True)

pdf_bytes = uploaded.read()

with st.spinner("Extrayendo texto del PDF..."):
    raw_text = extract_text_from_pdf_bytes(pdf_bytes)

opts = NormalizeOptions(
    remove_personal_data=remove_personal,
    remove_rubros_basura=remove_rubros,
    remove_nulls=remove_nulls,
)

clean_text = normalize_text(raw_text, opts)

st.success("Listo. Descargá el TXT/DOCX limpio.")

st.download_button(
    "⬇️ Descargar TXT limpio",
    data=clean_text.encode("utf-8"),
    file_name=uploaded.name.replace(".pdf", "") + "__CVAR_CLEAN.txt",
    mime="text/plain",
    use_container_width=True
)

docx_bytes = build_docx_bytes(clean_text)
st.download_button(
    "⬇️ Descargar DOCX limpio",
    data=docx_bytes,
    file_name=uploaded.name.replace(".pdf", "") + "__CVAR_CLEAN.docx",
    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    use_container_width=True
)
