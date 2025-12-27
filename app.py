# app.py
import streamlit as st
from normalizer import normalize_text

st.set_page_config(
    page_title="Normalizador de CVar (CONICET)",
    layout="centered"
)

st.title("Normalizador de CVar")
st.caption("PDF/TXT CONICET → texto limpio para valoración")

st.markdown(
"""
**Uso correcto**
1. Subí un TXT limpio del CVar (salida del PDF).
2. Presioná **Normalizar**.
3. Descargá el archivo limpio para el Valorador.
"""
)

uploaded_file = st.file_uploader(
    "Subir archivo TXT de CVar",
    type=["txt"]
)

if uploaded_file is not None:
    raw_text = uploaded_file.read().decode("utf-8", errors="ignore")

    st.success("Archivo cargado correctamente.")

    if st.button("Normalizar CVar"):
        with st.spinner("Normalizando texto..."):
            cleaned_text = normalize_text(raw_text)

        st.success("Normalización finalizada.")

        st.download_button(
            label="Descargar CVar limpio",
            data=cleaned_text,
            file_name=uploaded_file.name.replace(".txt", "__CVAR_CLEAN.txt"),
            mime="text/plain"
        )
