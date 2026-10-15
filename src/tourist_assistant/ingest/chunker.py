import re
from dataclasses import dataclass, field

from langchain_text_splitters import RecursiveCharacterTextSplitter

from tourist_assistant.ingest.loader import Line

# Librería Regular Expressions de Python para definir los patrones de búsqueda en el texto
_ZONE_RE = re.compile(r"^ZONA\s+(\w+)$")
_SECTION_RE = re.compile(r"^OTRAS VAINAS$")
_PLACE_RE = re.compile(r"^•\s*(.+)$")
_SUBITEM_RE = re.compile(r"^▪\s*(.+)$")
_BULLET_START_RE = re.compile(r"^[-o•▪]\s")
_LINK_RE = re.compile(
    r"\[(?:vídeo|ubicación|web|Tripadvisor)(?:\s*-\s*ubicación)?\]"
    r"|\(ubicación\)|[-–]\s*ubicación\s*[-–]?"
)


@dataclass(frozen=True)
class Chunk:
    """Fragmento del corpus listo para indexar"""

    id: str
    text: str
    metadata: dict = field(default_factory=dict)


def _short_name(raw: str) -> str:
    """Nombre del lugar sin dos puntos finales ni aclaraciones entre paréntesis del autor"""
    if raw.lower().startswith("sitios para comer"):
        return "Sitios para comer"
    return raw.strip(" :")


def _clean(text: str) -> str:
    """Elimina marcadores de enlace vacíos (ubicación) y espacios sobrantes"""
    text = _LINK_RE.sub("", text)
    return re.sub(r"[ \t]+", " ", text).replace(" .", ".").replace(" ,", ",").strip()


def _unwrap(lines: list[Line]) -> str:
    """Une los saltos de línea blandos del PDF; solo una viñeta abre línea nueva"""
    out: list[str] = []
    for line in lines:
        if out and not _BULLET_START_RE.match(line.text):
            out[-1] += " " + line.text
        else:
            out.append(line.text)
    return "\n".join(out)


def _page_range(lines: list[Line]) -> tuple[int, int]:
    return lines[0].page, lines[-1].page


def _build(chunk_id: str, header: str, lines: list[Line], zone: str, place: str) -> Chunk:
    page_start, page_end = _page_range(lines)
    body = _clean(_unwrap(lines)).removeprefix("• ")
    return Chunk(
        id=chunk_id,
        text=f"{header}\n{body}",
        metadata={
            "zone": zone,
            "place": place,
            "page_start": page_start,
            "page_end": page_end,
        },
    )


def _split_subitems(lines: list[Line]) -> list[tuple[str, list[Line]]]:
    """Divide un bloque en (nombre, líneas) por sub-viñetas; el preámbulo va aparte."""
    groups: list[tuple[str, list[Line]]] = [("", [])]
    for line in lines:
        match = _SUBITEM_RE.match(line.text)
        if match:
            name = re.split(r"\s*[(\[:]", match.group(1), maxsplit=1)[0].strip()
            groups.append((name, [line]))
        else:
            groups[-1][1].append(line)
    return [(name, grp) for name, grp in groups if grp]


def chunk_by_place(lines: list[Line], max_chars: int = 1800) -> list[Chunk]:
    """Genera un chunk por lugar, con metadatos zone, place y páginas

    Args:
        lines: líneas devueltas por :func:load_pdf_lines
        max_chars: por encima de este tamaño, el bloque se divide por viñetas cuadradas
    """
    blocks: list[tuple[str, str, list[Line]]] = []  # (zona, lugar, líneas)
    zone = "General"
    for line in lines:
        if zone_match := _ZONE_RE.match(line.text):
            zone = f"Zona {zone_match.group(1).capitalize()}"
        elif _SECTION_RE.match(line.text):
            zone = "Otras recomendaciones"
        elif place_match := _PLACE_RE.match(line.text):
            blocks.append((zone, _short_name(place_match.group(1)), [line]))
        elif blocks:
            blocks[-1][2].append(line)

    chunks: list[Chunk] = []
    for zone, place, block in blocks:
        text_len = sum(len(line.text) for line in block)
        subitems = _split_subitems(block) if text_len > max_chars else []
        if len(subitems) > 1:
            for name, group in subitems:
                label = f"{place} – {name}" if name else place
                header = f"[{zone} · {label}]"
                chunks.append(_build(f"c{len(chunks):03d}", header, group, zone, label))
        else:
            chunks.append(_build(f"c{len(chunks):03d}", f"[{zone} · {place}]", block, zone, place))
    return chunks


def chunk_recursive(lines: list[Line], size: int = 500, overlap: int = 100) -> list[Chunk]:
    """
    Corta por párrafos, líneas y espacios hasta size caracteres con overlap
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
    chunks: list[Chunk] = []
    for doc in splitter.create_documents([text]):
        start = doc.metadata["start_index"]
        end = start + len(doc.page_content) - 1
        chunks.append(
            Chunk(
                id=f"r{len(chunks):03d}",
                text=doc.page_content,
                metadata={
                    "zone": "",
                    "place": "",
                    "page_start": page_at[start],
                    "page_end": page_at[end],
                },
            )
        )
    return chunks
