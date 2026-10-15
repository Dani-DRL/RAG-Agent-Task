"""Ingesta: PDF → documentos (chunks) con metadatos zona, lugar y páginas."""

import re
from pathlib import Path
from typing import NamedTuple

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

# Viñetas que el extractor puede emitir en una línea aparte, separadas de su texto
_MARKERS = {"-", "o", "•", "▪"}
_ZONE_RE = re.compile(r"^ZONA\s+(\w+)$")
_PLACE_RE = re.compile(r"^•\s*(.+)$")
_SUBITEM_RE = re.compile(r"^▪\s*(.+)$")
_BULLET_RE = re.compile(r"^[-o•▪]\s")
_LINK_RE = re.compile(
    r"\[(?:vídeo|ubicación|web|Tripadvisor)(?:\s*-\s*ubicación)?\]"
    r"|\(ubicación\)|[-–]\s*ubicación\s*[-–]?"
)


class Line(NamedTuple):
    """Una línea del PDF y su página (1-indexada)"""

    text: str
    page: int


def load_pdf_lines(path: Path) -> list[Line]:
    """Extrae las líneas no vacías del PDF; una viñeta suelta se une a la línea siguiente"""
    lines: list[Line] = []
    marker = ""
    for page_number, page in enumerate(PdfReader(path).pages, start=1):
        for raw in (page.extract_text() or "").splitlines():
            text = raw.strip()
            if not text:
                continue
            if text in _MARKERS:
                marker = text
                continue
            lines.append(Line(f"{marker} {text}" if marker else text, page_number))
            marker = ""
    return lines


def _clean(text: str) -> str:
    """Quita marcadores de enlace ([vídeo], (ubicación)…) y espacios sobrantes"""
    text = _LINK_RE.sub("", text)
    return re.sub(r"[ \t]+", " ", text).replace(" .", ".").replace(" ,", ",").strip()


def _document(header: str, lines: list[Line], zone: str, place: str) -> Document:
    """Une los saltos de línea blandos (solo una viñeta abre línea nueva) y crea el Document"""
    paragraphs: list[str] = []
    for line in lines:
        if paragraphs and not _BULLET_RE.match(line.text):
            paragraphs[-1] += " " + line.text
        else:
            paragraphs.append(line.text)
    body = _clean("\n".join(paragraphs)).removeprefix("• ")
    return Document(
        page_content=f"[{header}]\n{body}",
        metadata={
            "zone": zone,
            "place": place,
            "page_start": lines[0].page,
            "page_end": lines[-1].page,
        },
    )


def chunk_by_place(lines: list[Line], max_chars: int = 1800) -> list[Document]:
    """Un documento por lugar (viñeta de primer nivel), con zona y páginas como metadatos

    Si un lugar supera max_chars se divide por sub-viñetas (p. ej. cada restaurante)
    """
    blocks: list[tuple[str, str, list[Line]]] = []  # (zona, lugar, líneas)
    zone = "General"
    for line in lines:
        if match := _ZONE_RE.match(line.text):
            zone = f"Zona {match.group(1).capitalize()}"
        elif line.text == "OTRAS VAINAS":
            zone = "Otras recomendaciones"
        elif match := _PLACE_RE.match(line.text):
            raw = match.group(1)
            place = "Sitios para comer" if raw.lower().startswith("sitios para comer") else raw
            blocks.append((zone, place.strip(" :"), [line]))
        elif blocks:
            blocks[-1][2].append(line)

    docs: list[Document] = []
    for zone, place, block in blocks:
        groups: list[tuple[str, list[Line]]] = [("", [])]  # (sub-lugar, líneas)
        if sum(len(line.text) for line in block) > max_chars:
            for line in block:
                if match := _SUBITEM_RE.match(line.text):
                    name = re.split(r"\s*[(\[:]", match.group(1), maxsplit=1)[0].strip()
                    groups.append((name, []))
                groups[-1][1].append(line)
        else:
            groups[0][1].extend(block)
        for name, group in groups:
            if group:
                label = f"{place} – {name}" if name else place
                docs.append(_document(f"{zone} · {label}", group, zone, label))
    return docs


def chunk_recursive(lines: list[Line], size: int = 500, overlap: int = 100) -> list[Document]:
    """Línea base: RecursiveCharacterTextSplitter de LangChain, ignorando la estructura

    La página de cada chunk se deduce de su posición en el texto concatenado
    """
    text = ""
    page_at: list[int] = []  # página de cada carácter
    for line in lines:
        piece = _clean(line.text) + "\n"
        text += piece
        page_at.extend([line.page] * len(piece))

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=size, chunk_overlap=overlap, add_start_index=True
    )
    docs = splitter.create_documents([text])
    for doc in docs:
        start = doc.metadata["start_index"]
        doc.metadata = {
            "page_start": page_at[start],
            "page_end": page_at[start + len(doc.page_content) - 1],
        }
    return docs
