# Normalizador de CVar (PDF CONICET → TXT/DOCX)

Repo 1 del flujo:

1) **Normalizador** (este repo): limpia el PDF de CVar (CONICET) y genera un **TXT/DOCX** “sin ruido”.
2) **Valorador** (repo 2): toma el TXT/DOCX limpio y realiza extracción + puntaje + categoría.

## Qué limpia (ejemplos reales)
- Encabezado repetido: `APELLIDO, NOMBRE` (en cada página)
- Pie: `CVar ES UNA INICIATIVA...` + `Fecha de generación`
- Números de página
- `null`
- Bullets / símbolos HTML tipo `&#61485;` (p. ej. en listados de títulos)

## Ejecutar (Streamlit)
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Ejecutar (CLI)
```bash
python normalizer.py "CVAR BEATRIZ FARAH.pdf" --outdir outputs
```

Genera:
- `outputs/<archivo>__CVAR_CLEAN.txt`
- `outputs/<archivo>__CVAR_CLEAN.docx`

## Ajustes
Si aparece un nuevo ruido, se agrega una regla simple en `normalizer.py` (regex).
