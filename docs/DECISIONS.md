# Registro de decisiones

Formato: contexto → opciones → decisión → consecuencias.

## D-001 · Entregable: núcleo Python + notebook (2026-10-15)
- Opciones: solo notebook; núcleo + notebook; juego web en TS.
- Decisión: paquete Python importable manejado desde un notebook. La web del profesor se descarta.
- Por qué: el enunciado exige notebook; la lógica modular puntúa en calidad de código y es testeable.

## D-002 · Orquestación: LangGraph (2026-10-15)
- Opciones evaluadas: PydanticAI, LangGraph, CrewAI, LlamaIndex, Smolagents, OpenAI Agents SDK, Google ADK, AutoGen, Haystack, DSPy.
- Decisión: LangGraph (grafo supervisor/router) por el bonus de agentes y memoria con checkpointer.
- Consecuencias: más boilerplate que PydanticAI. Mitigación: RAG, memoria y `get_weather` en módulos Python independientes del framework.
- Descartado: PydanticAI dentro de LangGraph (dos abstracciones de agente); CrewAI (oculta el flujo de control).

## D-003 · Modelos: Ollama primero, API después (2026-10-15)
- Chat `gemma4:e2b` (tool calling ya validado por el autor en otros proyectos), embeddings `embeddinggemma`, reranker opcional `bge-reranker-v2-m3`.
- Proveedor intercambiable vía `init_chat_model` y variables de entorno.

## D-004 · Hallazgo sobre el corpus: es muy pequeño (2026-10-15)
- `TENERIFE.pdf`: 25 páginas, ~16 000 caracteres (~4-5k tokens). Cabe entero en el contexto de cualquier modelo.
- Estructura: zonas (`ZONA NORTE`, ...) → viñetas por lugar (`• Santa Cruz de Tenerife:`) con sub-listas y enlaces "[ubicación]/[vídeo]".
- Implicación: RAG se justifica por el enunciado, no por necesidad. En el informe, comparar RAG vs. contexto completo como experimento y discutirlo como limitación.
- Plan de chunking: por lugar (viñeta de primer nivel) conservando metadatos zona + página; comparar con chunking de tamaño fijo en EXPERIMENTS.md.

## D-005 · Vector store: Chroma principal, FAISS como comparación (2026-10-15)
- Opciones: Chroma, FAISS, LanceDB, Qdrant local, pgvector, sqlite-vec, in-memory, servicios gestionados.
- Decisión: ChromaDB (persistencia en disco, filtrado por metadatos para citar zona/página). Detrás de una interfaz `VectorStore`, añadir FAISS (nombrado en el enunciado) y comparar tiempo de indexación, latencia y calidad de recuperación.
- Con ~150 chunks la diferencia de rendimiento será despreciable; la calidad depende más del chunking, embeddings y reranking. Hybrid BM25+vectores queda como experimento opcional.

## D-006 · Sin FastAPI por ahora; fachada `ChatService` + Gradio (2026-10-15)
- El notebook importa el paquete directamente; Gradio cubre el bonus web y el streaming en el mismo proceso.
- Modularidad por capas: dependencias hacia dentro (`graph/` usa `retrieval/`, `memory`, `tools/`, nunca al revés); interfaces en los puntos de cambio (VectorStore, factoría de proveedor LLM).
- `ChatService.chat(message, thread_id)` (y variante streaming) es el único punto de entrada para notebook, Gradio y un posible FastAPI futuro.
