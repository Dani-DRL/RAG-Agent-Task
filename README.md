# Asistente turístico de Tenerife

RAG + diálogo multiturno + function calling (`get_weather`) orquestado con LangGraph.
Desarrollo local con Ollama; proveedores de API (OpenAI/Gemini) seleccionables por configuración.

## Puesta en marcha

```bash
uv venv && uv pip install -e ".[dev,ui]"
cp .env.example .env
ollama pull gemma4:e2b && ollama pull embeddinggemma
```

## Estructura

- `src/tourist_assistant/` — núcleo (ingesta, vector store, memoria, herramientas, grafo)
- `notebooks/` — notebook principal
- `eval/` — conjunto reproducible de prompts y métricas
- `docs/` — `DECISIONS.md` (decisiones), `EXPERIMENTS.md` (pruebas), informe final
- `data/TENERIFE.pdf` — guía turística (corpus RAG)

(Se completará conforme avance el proyecto.)
