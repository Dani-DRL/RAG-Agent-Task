# Registro de experimentos

| ID | Fecha | Variable | Configuración | Resultado | Conclusión |
|----|-------|----------|---------------|-----------|------------|
| E-001 | 2026-10-15 | Librería de extracción PDF | PyMuPDF vs pypdf sobre TENERIFE.pdf | 16 224 vs 16 204 caracteres; 0,06 s vs 0,23 s; mismos 24 chunks | Equivalentes para este corpus; se elige pypdf (D-010) |
| E-002 | 2026-10-15 | Chunking (recuperación, k=4, 18 preguntas) | Por lugar (24) / recursivo 500-100 (40) / recursivo 1000-200 (19); embeddinggemma sin prefijos | hit@1 0,61 / 0,61 / 0,61; hit@3 0,83 / 0,67 / 0,78; MRR 0,71 / 0,64 / 0,69 | Por lugar es la mejor en hit@3 y MRR; los tres igualan en hit@1 |
| E-003 | 2026-10-15 | Prefijos de tarea de embeddinggemma | Mismas estrategias, con `task: search result \| query:` / `title: none \| text:` | por lugar: hit@1 0,78, hit@3 0,83, MRR 0,81; recursivos sin cambio | Los prefijos mejoran hit@1 en +0,17 y MRR en +0,10 con chunks por lugar; se activan por defecto (D-012) |
| E-004 | 2026-10-15 | Fallos de «por lugar» (diagnóstico a k=24) | Preguntas q01 (pizza Garachico), q11 (gofio), q18 (Buenavista) | rangos 6, 21 y 12; los chunks ganadores son los de comida | Chunks largos (Isla Baja 2260 car., La Orotava 1615) diluyen los detalles; probar a dividir lugares largos por sub-viñeta `o` |
