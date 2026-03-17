import argparse
import json
from pathlib import Path

import faiss
import numpy as np

from rag.embeddings import get_encoder


def build_index(docs_path: str, index_path: str, meta_path: str):
    docs = []
    for txt in Path(docs_path).glob("*.txt"):
        content = txt.read_text(encoding="utf-8").strip()
        for paragraph in [p.strip() for p in content.split("\n\n") if p.strip()]:
            docs.append({"source": txt.name, "text": paragraph})

    encoder = get_encoder()
    embs = encoder.encode([d["text"] for d in docs], normalize_embeddings=True)
    arr = np.array(embs, dtype=np.float32)

    index = faiss.IndexFlatIP(arr.shape[1])
    index.add(arr)
    faiss.write_index(index, index_path)
    Path(meta_path).write_text(json.dumps(docs, indent=2), encoding="utf-8")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--docs", default="knowledge_base/sample_docs")
    p.add_argument("--index", default="knowledge_base/faiss.index")
    p.add_argument("--meta", default="knowledge_base/faiss_meta.json")
    args = p.parse_args()
    build_index(args.docs, args.index, args.meta)
