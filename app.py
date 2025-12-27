# -*- coding: utf-8 -*-
import streamlit as st
from pathlib import Path

from normalizer import normalize_pdf

st.set_page_config(page_title="Normalizador de CVar (PDF CONICET)", layout="wide")
st.title("Normalizador de CVar — UCCuyo / SIyVT")
st.caption("Subí un PDF (CVar CONICET). La app elimina ruido típico del PDF y genera TXT + DOCX listos para el repo 2 (Valorador).")

uploaded = st.file_uploader("Cargar PDF de CVar", type=["pdf"])

if uploaded:
    tmp_dir = Path("tmp")
    tmp_dir.mkdir(exist_ok=True)
    tmp_pdf = tmp_dir / uploaded.name
    tmp_pdf.write_bytes(uploaded.getvalue())

    txt_path, docx_path = normalize_pdf(tmp_pdf, Path("outputs"))

    clean_text = txt_path.read_text(encoding="utf-8")
    col1, col2 = st.columns([2, 1], gap="large")

    with col1:
        st.subheader("Vista previa (texto normalizado)")
        st.text_area("CVar limpio", value=clean_text, height=560)

    with col2:
        st.subheader("Descargas")
        st.download_button(
            "Descargar TXT",
            data=clean_text.encode("utf-8"),
            file_name=txt_path.name,
            mime="text/plain",
            use_container_width=True
        )
        st.download_button(
            "Descargar DOCX",
            data=docx_path.read_bytes(),
            file_name=docx_path.name,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True
        )
        st.divider()
        st.caption("El TXT es el insumo más estable para segmentación y scoring automático.")
else:
    st.info("Cargá un PDF para generar el CVar normalizado.")
