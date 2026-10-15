"""Embeddings e índice vectorial (Chroma, distancia coseno)"""

from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings

from tourist_assistant.config import Settings


class TaskPrefixEmbeddings(OllamaEmbeddings):
    """embeddinggemma rinde mejor con prefijos distintos para consulta y documento (E-003)"""

    def embed_query(self, text: str) -> list[float]:
        # embed_query de OllamaEmbeddings llama a embed_documents (que añadiría el prefijo
        # de documento), así que se salta nuestro override con la clase base
        return OllamaEmbeddings.embed_documents(self, [f"task: search result | query: {text}"])[0]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return OllamaEmbeddings.embed_documents(self, [f"title: none | text: {t}" for t in texts])


def get_embeddings(settings: Settings, task_prefixes: bool = True) -> OllamaEmbeddings:
    """Embeddings de Ollama; con prefijos de tarea si el modelo es embeddinggemma"""
    cls = TaskPrefixEmbeddings if task_prefixes else OllamaEmbeddings
    return cls(model=settings.embed_model, base_url=settings.ollama_base_url)


def build_index(
    docs: list[Document], embeddings, name: str = "tenerife", persist_dir: Path | None = None
) -> Chroma:
    """Indexa los documentos en una colección Chroma (en memoria si no hay persist_dir)"""
    return Chroma.from_documents(
        docs,
        embeddings,
        collection_name=name,
        persist_directory=str(persist_dir) if persist_dir else None,
        collection_metadata={"hnsw:space": "cosine"},
    )
