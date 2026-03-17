import json
from pathlib import Path

import faiss
import numpy as np

from rag.embeddings import get_encoder


class KnowledgeBaseService:
    def __init__(self, index_path: str, meta_path: str):
        self.index_path = Path(index_path)
        self.meta_path = Path(meta_path)
        self.index = None
        self.meta: list[dict] = []

    async def load(self):
        if self.index_path.exists() and self.meta_path.exists():
            self.index = faiss.read_index(str(self.index_path))
            self.meta = json.loads(self.meta_path.read_text())
            return
        self.index = faiss.IndexFlatIP(384)
        self.meta = []

    async def search(self, query: str, top_k: int = 3) -> str:
        if self.index is None or not self.meta:
            return ""
        encoder = get_encoder()
        vec = encoder.encode([query], normalize_embeddings=True)
        distances, indices = self.index.search(np.array(vec, dtype=np.float32), top_k)
        _ = distances
        hits = []
        for idx in indices[0]:
            if idx == -1:
                continue
            hits.append(self.meta[idx]["text"])
        return "\n".join(hits)
