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

## D-007 · Sin API key de momento: Ollama hasta el final del desarrollo (2026-10-15)
- El autor aún no tiene clave de OpenAI/Gemini. Todo el desarrollo y las pruebas usan Ollama.
- El enunciado pide un LLM comercial: la factoría de proveedor (`llm.py`) debe mantenerse intercambiable por configuración y la conexión API se verifica en cuanto haya clave. Riesgo asumido: no haber probado aún los límites reales de una API.

## D-008 · `get_weather(fecha)`: validación de fecha y fallback (2026-10-15)
- Open-Meteo `forecast` cubre ~16 días hacia delante; el histórico requiere la API `archive`.
- Decisión: validar la fecha primero (formato, pasado, fuera de rango) y devolver errores claros y tipados; fallback a datos simulados deterministas cuando falle la red. Cada intento se registra en log.

## D-009 · Chunking por lugar: implementación (2026-10-15)
- `ingest/loader.py` extrae líneas con página y fusiona viñetas sueltas; `ingest/chunker.py` genera 24 chunks de 105–2260 caracteres (12 lugares + sección de comida dividida por restaurante cuando supera 1800 caracteres).
- Se eliminan marcadores de enlace (`[vídeo]`, `[ubicación]`…) porque son ruido para el embedding; cada chunk lleva cabecera `[Zona · Lugar]` y metadatos `zone`, `place`, `page_start`, `page_end` para la cita.
- Se descarta el primer contexto del autor ("sobre todo os podré decir de zona norte") del nombre del lugar y se normaliza a "Sitios para comer".
- Línea base para el experimento de comparación: ver D-011.
- Limitación: los lugares con subapartados (Costa Adeje, Isla Baja) superan los 2000 caracteres y mezclan varios sitios en un chunk; se evaluará si dividirlos mejora la recuperación.

## D-010 · Extracción del PDF: pypdf en lugar de PyMuPDF (2026-10-15)
- Medido sobre `TENERIFE.pdf`: PyMuPDF 16 224 caracteres en 0,06 s; pypdf 16 204 caracteres en 0,23 s. Texto prácticamente idéntico.
- Decisión: pypdf (dependencia pura Python, la misma que se vio en clase). Con él se obtienen exactamente los mismos 24 chunks por lugar, y los tests pasan sin cambios.
- Sustituye a la mención de PyMuPDF en la fase de scaffolding. La extracción queda aislada en `load_pdf_lines`, por lo que cambiar de librería no afecta al chunker.

## D-011 · Línea base de chunking: RecursiveCharacterTextSplitter de LangChain (2026-10-15)
- Sustituye a la ventana fija escrita a mano: es el splitter visto en clase y el más reconocible para el informe (`chunk_recursive`, dependencia `langchain-text-splitters`).
- Se mantiene `chunk_by_place` como estrategia principal: el splitter genérico no conoce la estructura zona → lugar y mezcla lugares en un mismo chunk (p. ej. el chunk 3 acaba con el título de «Parque rural de Anaga»).
- Con 500/100 produce 40 chunks (205–499 caracteres) y con 1000/200 produce 19 (863–997). La página se deduce con `add_start_index`; zona y lugar quedan vacíos, por lo que la cita solo puede dar la página.
- A comparar en EXPERIMENTS.md: por lugar (24) vs recursivo 500/100 vs recursivo 1000/200 vs contexto completo.

## D-012 · Recuperación: Chroma coseno y prefijos de tarea (2026-10-15)
- `retrieval.py`: `get_embeddings()` (Ollama; con prefijos de tarea `task: search result | query:` / `title: none | text:` si se pide) y `build_index()` sobre `langchain_chroma.Chroma` con distancia coseno. Sin interfaz propia; se usa la API de LangChain (`similarity_search`, `similarity_search_with_score`).
- E-003: los prefijos mejoran hit@1 en +0,17 con chunks por lugar; quedan activos por defecto.
- Cuidado: `OllamaEmbeddings.embed_query` llama internamente a `embed_documents`; la subclase con prefijos debe saltarse su propio override o la consulta recibe ambos prefijos (hit@1 baja de 0,78 a 0,67). Hay un test que lo vigila.
- Evaluación independiente del chunking: `eval/retrieval_questions.json` (18 preguntas con fragmentos esperados) y `evaluation.py` (hit@1, hit@3, MRR, latencia). Un acierto es que algún chunk del top-k contenga el texto esperado.
- Limitación: 18 preguntas escritas por el propio autor del código, todas con respuesta en el corpus; no mide el rechazo de preguntas fuera de tema (se evaluará aparte).
- Pendiente: dividir lugares largos (E-004), FAISS opcional, reranker y contexto completo como comparación.

## D-013 · Simplificación: módulos planos y tipos de LangChain (2026-10-15)
- Se eliminan las abstracciones prematuras: `Chunk`, `SearchResult`, el Protocol `VectorStore` y el wrapper `ChromaStore`. Los chunkers devuelven `langchain_core.documents.Document` y el índice es un `Chroma` de LangChain.
- `ingest/`, `retrieval/` y `evaluation/` pasan de paquetes a un módulo cada uno (`ingest.py`, `retrieval.py`, `evaluation.py`). Se mantiene `chunk_by_place` (aporta valor medido, E-002) y el conjunto de preguntas.
- Si más adelante se añade FAISS, bastará cambiar la construcción del índice (misma API de LangChain); no hace falta abstracción por adelantado.
- Criterio general: no crear capas, clases ni paquetes hasta que haya un segundo uso real. Esto también aplica al resto del plan (`ChatService`, `graph/`).
