"""Evaluación de la recuperación con preguntas de respuesta conocida

Cada pregunta lleva una lista expected de fragmentos de texto; hay acierto si alguno
aparece en un chunk recuperado. Así sirve para comparar estrategias de chunking.
"""

import json
import time
from pathlib import Path


def evaluate_retrieval(store, questions_path: Path, k: int = 4) -> dict:
    """Devuelve hit@1, hit@3, MRR, latencia media (ms) y los ids de preguntas falladas"""
    questions = json.loads(questions_path.read_text(encoding="utf-8"))
    ranks, latencies = [], []
    for q in questions:
        start = time.perf_counter()
        hits = store.similarity_search(q["question"], k=k)
        latencies.append(time.perf_counter() - start)
        rank = next(
            (
                i
                for i, doc in enumerate(hits, start=1)
                if any(e.lower() in doc.page_content.lower() for e in q["expected"])
            ),
            None,
        )
        ranks.append(rank)
    n = len(questions)
    return {
        "hit@1": sum(r == 1 for r in ranks) / n,
        "hit@3": sum(r is not None and r <= 3 for r in ranks) / n,
        "mrr": sum(1 / r for r in ranks if r) / n,
        "latency_ms": 1000 * sum(latencies) / n,
        "missed": [q["id"] for q, r in zip(questions, ranks) if r is None],
    }
