# -*- coding: utf-8 -*-
"""
Normalizador de CVar (PDF descargado desde CONICET)

- Extrae texto desde PDF (pdfplumber)
- Elimina encabezados/pies repetidos, números de página, artefactos HTML (&#61485;), líneas 'null'
- Normaliza saltos de línea para facilitar extracción y puntaje en el repo 2 (Valorador)
- Exporta TXT + DOCX

CLI:
    python normalizer.py "CVAR.pdf" --outdir outputs
"""
from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

import pdfplumber
from docx import Document
from docx.oxml.ns import qn

RE_PAGE_NUMBER = re.compile(r"^\s*\d+\s*$")
RE_CVAR_FOOTER = re.compile(r"^\s*CVar\s+ES\s+UNA\s+INICIATIVA\s+DEL\s+MINISTERIO\s+DE\s+CIENCIA", re.IGNORECASE)
RE_FECHA_GENERACION = re.compile(r"^\s*Fecha\s+de\s+generaci[oó]n\s*:\s*\d{1,2}/\d{1,2}/\d{4}\s*$", re.IGNORECASE)
RE_HTML_ENTITY = re.compile(r"&#\d+;")
RE_NULL_LINE = re.compile(r"^\s*null\.?\s*$", re.IGNORECASE)

RE_NAME_HEADER = re.compile(r"^\s*[A-ZÁÉÍÓÚÑÜ][A-ZÁÉÍÓÚÑÜ\s\-']+,\s*[A-ZÁÉÍÓÚÑÜ][A-ZÁÉÍÓÚÑÜ\s\-']+\s*$")

RE_DATE_RANGE_1 = re.compile(r"^\s*\d{2}/\d{4}\s*-\s*(\d{2}/\d{4}|\d{4}|Actualidad)\b", re.IGNORECASE)
RE_DATE_RANGE_2 = re.compile(r"^\s*\d{4}\s*-\s*(\d{4}|Actualidad)\b", re.IGNORECASE)
RE_EVENTO = re.compile(r"^\s*\d{4}\s*-\s*Evento:\s*", re.IGNORECASE)
RE_ANIO_FINAL = re.compile(r"^\s*Año\s+de\s+finalizaci[oó]n\s*:\s*(19\d{2}|20\d{2}|\d{2}/\d{4})\s*$", re.IGNORECASE)

RE_SECTION = re.compile(
    r"^\s*(DATOS PERSONALES|FORMACION ACAD[ÉE]MICA|FORMACION COMPLEMENTARIA|ANTECEDENTES EN CYT|"
    r"Formaci[oó]n de recursos humanos|Financiamiento CyT|Actividades de Evaluaci[oó]n y Gesti[oó]n Editorial|"
    r"Actividades de Extensi[oó]n|Actividades profesionales|Participaci[oó]n en eventos CyT|PUBLICACIONES|Premios)\s*$",
    re.IGNORECASE
)
RE_ALL_CAPS = re.compile(r"^[A-ZÁÉÍÓÚÑÜ0-9 ,\-\(\)\/]{5,70}$")


@dataclass
class NormalizationConfig:
    join_hyphenated_words: bool = True
    max_blank_lines: int = 1


def extract_text_from_pdf(pdf_path: Path) -> str:
    pages: List[str] = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page in pdf.pages:
            pages.append(page.extract_text() or "")
    return "\n\n<<<PAGE_BREAK>>>\n\n".join(pages)


def _detect_name_header(text: str) -> Optional[str]:
    first_page = text.split("<<<PAGE_BREAK>>>", 1)[0]
    for ln in first_page.splitlines():
        ln = ln.strip()
        if not ln:
            continue
        if RE_NAME_HEADER.match(ln):
            return ln
        break
    return None


def _clean_lines(lines: Iterable[str], detected_name: Optional[str]) -> List[str]:
    out: List[str] = []
    for raw in lines:
        line = (raw or "").strip()
        if not line:
            out.append("")
            continue
        if RE_PAGE_NUMBER.match(line): 
            continue
        if RE_CVAR_FOOTER.match(line): 
            continue
        if RE_FECHA_GENERACION.match(line): 
            continue
        if RE_NULL_LINE.match(line): 
            continue
        if detected_name and line == detected_name:
            continue

        line = RE_HTML_ENTITY.sub("", line)
        line = re.sub(r"\s+", " ", line).strip()
        out.append(line)
    return out


def _should_force_new_paragraph(line: str) -> bool:
    if not line:
        return True
    if RE_SECTION.match(line) or (RE_ALL_CAPS.match(line) and len(line) <= 70):
        return True
    if RE_DATE_RANGE_1.match(line) or RE_DATE_RANGE_2.match(line) or RE_EVENTO.match(line):
        return True
    if RE_ANIO_FINAL.match(line):
        return True
    if line.lower().startswith("rol:"):
        return True
    if re.match(r"^(Organizada por|Ejecutado en|Financiado por|Direcci[oó]n|Instituci[oó]n de ejecuci[oó]n|Tareas realizadas)\s*:", line, re.IGNORECASE):
        return True
    return False


def normalize_text(raw_text: str, cfg: Optional[NormalizationConfig] = None) -> str:
    cfg = cfg or NormalizationConfig()
    detected_name = _detect_name_header(raw_text)

    pages = raw_text.split("<<<PAGE_BREAK>>>")
    all_lines: List[str] = []
    for p in pages:
        all_lines.extend(_clean_lines(p.splitlines(), detected_name))
        all_lines.append("")

    # unir palabras cortadas con guión al final de línea
    if cfg.join_hyphenated_words:
        merged: List[str] = []
        i = 0
        while i < len(all_lines):
            ln = all_lines[i]
            if ln.endswith("-") and i + 1 < len(all_lines):
                nxt = all_lines[i + 1]
                if nxt and not _should_force_new_paragraph(nxt):
                    merged.append(ln[:-1] + nxt.lstrip())
                    i += 2
                    continue
            merged.append(ln)
            i += 1
        all_lines = merged

    out_lines: List[str] = []
    for ln in all_lines:
        if not out_lines:
            out_lines.append(ln)
            continue

        if ln == "":
            if out_lines and out_lines[-1] == "":
                continue
            out_lines.append("")
            continue

        if _should_force_new_paragraph(ln) or out_lines[-1] == "":
            out_lines.append(ln)
        else:
            out_lines[-1] = (out_lines[-1] + " " + ln).strip()

    # compactar blancos
    compacted: List[str] = []
    blank_run = 0
    for ln in out_lines:
        if ln == "":
            blank_run += 1
            if blank_run <= cfg.max_blank_lines:
                compacted.append("")
        else:
            blank_run = 0
            compacted.append(ln)

    return "\n".join(compacted).strip() + "\n"


def export_docx(clean_text: str, out_path: Path) -> None:
    """
    Export DOCX robusto (sin setear fuentes para evitar errores en Streamlit Cloud).
    """
    from docx import Document

    doc = Document()
    for line in clean_text.split("\n"):
        doc.add_paragraph(line)
    doc.save(str(out_path))


def normalize_pdf(pdf_path: Path, outdir: Path) -> Tuple[Path, Path]:
    outdir.mkdir(parents=True, exist_ok=True)
    raw = extract_text_from_pdf(pdf_path)
    clean = normalize_text(raw)

    stem = pdf_path.stem.replace(" ", "_")
    txt_path = outdir / f"{stem}__CVAR_CLEAN.txt"
    docx_path = outdir / f"{stem}__CVAR_CLEAN.docx"

    txt_path.write_text(clean, encoding="utf-8")
    export_docx(clean, docx_path)
    return txt_path, docx_path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf", type=str, help="Ruta al PDF del CVar")
    ap.add_argument("--outdir", type=str, default="outputs", help="Directorio de salida")
    args = ap.parse_args()

    pdf_path = Path(args.pdf).expanduser().resolve()
    outdir = Path(args.outdir).expanduser().resolve()

    if not pdf_path.exists():
        raise SystemExit(f"No existe el archivo: {pdf_path}")

    txt_path, docx_path = normalize_pdf(pdf_path, outdir)
    print(f"OK\n- TXT:  {txt_path}\n- DOCX: {docx_path}")


if __name__ == "__main__":
    main()
