import hashlib
import json
from unittest.mock import patch

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_ollama import OllamaEmbeddings

from tourist_assistant.evaluation import evaluate_retrieval
from tourist_assistant.retrieval import TaskPrefixEmbeddings, build_index


class FakeEmbeddings(Embeddings):
    """Bolsa de palabras hasheadas, determinista y sin Ollama"""

    def _embed(self, text):
        vec = [0.0] * 64
        for word in text.lower().split():
            vec[int(hashlib.md5(word.encode()).hexdigest(), 16) % 64] += 1.0
        return vec

    def embed_documents(self, texts):
        return [self._embed(t) for t in texts]

    def embed_query(self, text):
        return self._embed(text)


def test_index_search_and_evaluation(tmp_path):
    docs = [
        Document(page_content="playa arena negra atardecer Benijo", metadata={"page_start": 8}),
        Document(page_content="parque acuático Siam Park olas", metadata={"page_start": 21}),
    ]
    store = build_index(docs, FakeEmbeddings(), name="test")
    top = store.similarity_search("atardecer en Benijo", k=1)[0]
    assert top.metadata["page_start"] == 8

    questions = tmp_path / "q.json"
    questions.write_text(
        json.dumps(
            [
                {"id": "a", "question": "parque acuático", "expected": ["Siam Park"]},
                {"id": "b", "question": "pastelería", "expected": ["no existe"]},
            ]
        )
    )
    result = evaluate_retrieval(store, questions, k=2)
    assert result["hit@1"] == 0.5 and result["missed"] == ["b"]


def test_task_prefixes_are_not_mixed():
    sent = []
    emb = TaskPrefixEmbeddings(model="x")
    with patch.object(
        OllamaEmbeddings, "embed_documents", lambda self, t: sent.append(t) or [[0.0]]
    ):
        emb.embed_query("hola")
        emb.embed_documents(["texto"])
    assert sent == [["task: search result | query: hola"], ["title: none | text: texto"]]
