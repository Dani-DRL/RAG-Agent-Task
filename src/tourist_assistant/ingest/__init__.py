"""Ingesta: PDF → chunks con metadatos."""

from tourist_assistant.ingest.chunker import Chunk, chunk_by_place, chunk_recursive
from tourist_assistant.ingest.loader import Line, load_pdf_lines

__all__ = ["Chunk", "Line", "chunk_by_place", "chunk_recursive", "load_pdf_lines"]
