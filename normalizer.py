# app.py
import streamlit as st

from normalizer import (
    NormalizeOptions,
    extract_text_from_pdf_bytes,
    normalize_text,
    build_docx_bytes,
)

st.set_page_config(page_title="Normalizador de CVar (CONICET)", layout="wide")
st.title("Normalizador de CVar (PDF CONICET → TXT/DOCX)")
st.caption("Limpia ruido de PDF y elimina DATOS PERSONALES. Genera TXT y DOCX listos para el Valorador (Repo 2).")

with st.expander("Opciones (recomendado dejar por defecto)", expanded=False):
    remove_personal = st.checkbox("Eliminar bloque DATOS PERSONALES (recomendado)", value=True)
    remove_rubros = st.checkbox("Eliminar rótulos basura (ej. 'TECNOLOGÍA E INNOVACIÓN')", value=True)
    remove_nulls = st.checkbox("Eliminar 'null' / 'null(ed)'", value=True)
    join_lines = st.checkbox("Unir líneas cortadas por el PDF (recomendado)", value=True)

uploaded = st.file_uploader("Subí el PDF CVar descargado de CONICET", type=["pdf"])

if uploaded:
    pdf_bytes = uploaded.read()

    with st.spinner("Extrayendo texto del PDF..."):
        raw_text = extract_text_from_pdf_bytes(pdf_bytes)

    opts = NormalizeOptions(
        remove_personal_data=remove_personal,
        remove_rubros_basura=remove_rubros,
        remove_nulls=remove_nulls,
        aggressive_join_lines=join_lines,
    )

    with st.spinner("Normalizando texto..."):
        clean_text = normalize_text(raw_text, opts=opts)

    st.success("Listo. Descargá el TXT/DOCX limpio.")

    col1, col2 = st.columns([1, 1])
    with col1:
        st.download_button(
            label="⬇️ Descargar TXT limpio",
            data=clean_text.encode("utf-8"),
            file_name=f"{uploaded.name.replace('.pdf','')}__CVAR_CLEAN.txt",
            mime="text/plain",
        )

    with col2:
        docx_bytes = build_docx_bytes(clean_text)
        st.download_button(
            label="⬇️ Descargar DOCX limpio (auditoría)",
            data=docx_bytes,
            file_name=f"{uploaded.name.replace('.pdf','')}__CVAR_CLEAN.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

    st.divider()
    st.subheader("Vista previa del texto limpio (primeras 250 líneas)")
    preview_lines = clean_text.splitlines()[:250]
    st.text("\n".join(preview_lines))
