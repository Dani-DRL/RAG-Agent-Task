"""Lectura del PDF como líneas limpias con su número de página"""

from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader

# Viñetas que el extractor puede emitir en una línea aparte, separadas de su texto.
_MARKERS = {"-", "o", "•", "▪"}


@dataclass(frozen=True)
class Line:
    """Una línea de texto del PDF y la página (1-indexada) de la que procede"""

    text: str
    page: int


def load_pdf_lines(path: Path) -> list[Line]:
    """Extrae las líneas del PDF, unificando viñetas sueltas con su texto.
    Descarta líneas vacías. Una viñeta aislada (``-``, ``o``, ``•``, ``▪``) se
    fusiona con la línea siguiente, aunque esta caiga en la página siguiente.
    """
    lines: list[Line] = []
    pending_marker: str | None = None
    for page_number, page in enumerate(PdfReader(path).pages, start=1):
        for raw in (page.extract_text() or "").splitlines():
            text = raw.strip()
            if not text:
                continue
            if text in _MARKERS:
                pending_marker = text
                continue
            if pending_marker:
                text = f"{pending_marker} {text}"
                pending_marker = None
            lines.append(Line(text=text, page=page_number))
    return lines
