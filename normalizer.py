import re
from dataclasses import dataclass
from typing import Optional

RE_DATOS_PERSONALES = re.compile(
    r"DATOS\s+PERSONALES[\s\S]*?FORMACI[ÓO]N\s+ACAD[ÉE]MICA",
    re.IGNORECASE
)
RE_RUBRO_BASURA = re.compile(
    r"^\s*TECNOLOG[IÍ]A\s+E\s+INNOVACI[ÓO]N\s*$",
    re.IGNORECASE | re.MULTILINE
)
RE_NULLS = re.compile(r"\bnull(?:\s*\(ed\))?\b", re.IGNORECASE)
RE_MANY_NEWLINES = re.compile(r"\n{3,}")

@dataclass
class NormalizeOptions:
    remove_personal_data: bool = True
    remove_rubros_basura: bool = True
    remove_nulls: bool = True

def normalize_text(raw_text: str, opts: Optional[NormalizeOptions] = None) -> str:
    opts = opts or NormalizeOptions()
    text = (raw_text or "").replace("\r\n", "\n").replace("\r", "\n")
    if opts.remove_personal_data:
        text = RE_DATOS_PERSONALES.sub("FORMACIÓN ACADÉMICA\n", text)
    if opts.remove_rubros_basura:
        text = RE_RUBRO_BASURA.sub("", text)
    if opts.remove_nulls:
        text = RE_NULLS.sub("", text)
    text = RE_MANY_NEWLINES.sub("\n\n", text).strip() + "\n"
    return text

def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    import io
    import pdfplumber
    parts = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            parts.append(page.extract_text() or "")
    return "\n".join(parts)

def build_docx_bytes(clean_text: str) -> bytes:
    import io
    from docx import Document
    doc = Document()
    for line in clean_text.split("\n"):
        doc.add_paragraph(line)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()
