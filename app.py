import json
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

st.set_page_config(page_title="Normalizador de CVar (PDF → estructurado)", layout="wide")
st.title("Normalizador de CVar (PDF → estructurado)")
st.caption(
    "Entrada: PDF descargado desde CONICET. "
    "Salidas: __CVAR_CLEAN.txt + __CVAR_CLEAN.docx (estructurado por secciones) "
    "+ opcional __CVAR_STRUCTURED.json (para puntuar sin regex infinitas)."
)

uploaded = st.file_uploader("Subí el PDF del CVar (CONICET)", type=["pdf"])

if not uploaded:
    st.info("Esperando PDF...")
    st.stop()

pdf_bytes = uploaded.read()

with st.expander("Opciones de normalización", expanded=False):
    remove_personal_data = st.checkbox("Eliminar Datos Personales", value=True)
    remove_rubros_basura = st.checkbox("Eliminar rubros basura (p.ej. 'TECNOLOGÍA E INNOVACIÓN')", value=True)
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
        parsed_formacion = parse_formacion_academica(sections.get("FORMACIÓN ACADÉMICA", ""))

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

st.success("Listo: se generó el TXT limpio y el DOCX estructurado." + (" También el JSON estructurado." if export_json else ""))

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
        use_container_width=True,
    )

with c2:
    st.download_button(
        "⬇️ Descargar DOCX estructurado (__CVAR_CLEAN.docx)",
        data=docx_bytes,
        file_name=docx_name,
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        use_container_width=True,
    )

with c3:
    if export_json and structured is not None:
        st.download_button(
            "⬇️ Descargar JSON estructurado (__CVAR_STRUCTURED.json)",
            data=json.dumps(structured, ensure_ascii=False, indent=2).encode("utf-8"),
            file_name=json_name,
            mime="application/json; charset=utf-8",
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
        st.info("Se encontró el bloque de Formación académica, pero no se pudieron separar entradas (revisar formato del PDF).")

# -------------------------
# Vista previa (por secciones)
# -------------------------
st.markdown("---")
st.subheader("Vista previa")

tab1, tab2, tab3 = st.tabs(["TXT limpio (primeras líneas)", "Secciones (vista)", "Formación académica (detalle)"])

with tab1:
    st.code("\n".join(clean_text.splitlines()[:250]) or "(archivo vacío)", language="text")

with tab2:
    if not sections:
        st.info("No se detectaron secciones.")
    else:
        chosen = st.selectbox("Elegí una sección para ver el bloque:", options=sec_names, index=0)
        block = sections.get(chosen, "")
        st.code("\n".join(block.splitlines()[:400]) or "(bloque vacío)", language="text")

with tab3:
    if not parsed_formacion:
        st.info("No se detectó / no se pudo parsear Formación académica.")
    else:
        tipo = st.selectbox(
            "Tipo dentro de Formación:",
            options=[k for k in ["DOCTORADO", "MAESTRÍA", "ESPECIALIZACIÓN", "GRADO", "PROFESORADO", "DIPLOMATURA", "ESTANCIA", "OTRO"]],
            index=0
        )
        items = parsed_formacion.get(tipo, [])
        st.write(f"Entradas: **{len(items)}**")
        for i, it in enumerate(items[:30], start=1):
            titulo = it.get("titulo", "").strip()
            fin = "FINALIZADO" if it.get("finalizado") else "NO FINALIZADO / EN CURSO"
            st.markdown(f"**{i}. {titulo}** — {fin}")
            st.code((it.get("texto") or "").strip()[:2000], language="text")
