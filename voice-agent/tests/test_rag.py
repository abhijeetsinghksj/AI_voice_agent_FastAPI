import asyncio
import json

import pytest

np = pytest.importorskip("numpy")
faiss = pytest.importorskip("faiss")

from rag.kb_service import KnowledgeBaseService


class DummyEncoder:
    def encode(self, texts, normalize_embeddings=True):
        _ = texts, normalize_embeddings
        return np.array([[1.0, 0.0, 0.0]], dtype=np.float32)


def test_kb_search(tmp_path, monkeypatch):
    async def run_case():
        index_path = tmp_path / "faiss.index"
        meta_path = tmp_path / "faiss_meta.json"
        index = faiss.IndexFlatIP(3)
        index.add(np.array([[1.0, 0.0, 0.0]], dtype=np.float32))
        faiss.write_index(index, str(index_path))
        meta_path.write_text(json.dumps([{"text": "hello world"}]))

        monkeypatch.setattr("rag.kb_service.get_encoder", lambda: DummyEncoder())
        kb = KnowledgeBaseService(str(index_path), str(meta_path))
        await kb.load()
        out = await kb.search("hello", top_k=1)
        assert "hello world" in out

    asyncio.run(run_case())
