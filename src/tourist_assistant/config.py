"""Configuración central del proyecto.

Es el único módulo que lee variables de entorno (o ``.env``). El resto del
paquete recibe un objeto :class:`Settings` y nunca toca ``os.environ``.
"""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Ajustes del asistente, sobreescribibles por variables de entorno."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- Proveedor LLM ---
    llm_provider: str = Field("ollama", description="ollama | openai | google_genai")
    llm_model: str = "gemma4:e2b"
    embed_model: str = "embeddinggemma"
    ollama_base_url: str = "http://localhost:11434"
    openai_api_key: str | None = None
    google_api_key: str | None = None

    # --- Parámetros de generación (expuestos según el enunciado) ---
    temperature: float = Field(0.2, ge=0.0, le=2.0)
    top_p: float = Field(0.9, gt=0.0, le=1.0)
    max_tokens: int = Field(1024, gt=0)

    # --- Rutas ---
    pdf_path: Path = PROJECT_ROOT / "data" / "TENERIFE.pdf"
    chroma_dir: Path = PROJECT_ROOT / "chroma_db"
    log_dir: Path = PROJECT_ROOT / "logs"


@lru_cache
def get_settings() -> Settings:
    """Devuelve los ajustes (cacheados) del proceso."""
    return Settings()
