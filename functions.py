import os
import json
from pathlib import Path
from typing import Dict

import numpy as np
import faiss
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

VECTOR_STORE_DIR = Path("vector_store")
EMBED_MODEL = "text-embedding-3-small"

_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Lazy-loaded singletons — populated on first call to tyre_semantic_search
_index: faiss.IndexFlatIP | None = None
_metadata: list[dict] | None = None


def _load_vector_store():
    global _index, _metadata
    if _index is None:
        _index = faiss.read_index(str(VECTOR_STORE_DIR / "index.faiss"))
        _metadata = json.loads((VECTOR_STORE_DIR / "metadata.json").read_text(encoding="utf-8"))


def _embed(text: str) -> np.ndarray:
    response = _client.embeddings.create(model=EMBED_MODEL, input=[text])
    vec = np.array(response.data[0].embedding, dtype=np.float32)
    norm = np.linalg.norm(vec)
    return (vec / norm).reshape(1, -1)


def tyre_semantic_search(query: str, top_k: int = 10) -> list[dict]:
    """Search the vector store for tyre-vehicle mappings matching the query.

    Returns up to top_k chunks with their similarity score and source text.
    """
    _load_vector_store()
    query_vec = _embed(query)
    scores, indices = _index.search(query_vec, top_k)
    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:
            continue
        entry = _metadata[idx]
        results.append({
            "score": round(float(score), 4),
            "source": entry["source"],
            "chunk_index": entry["chunk_index"],
            "text": entry["text"],
        })
    return results


def product_details(sku: int) -> Dict | None:
    df = pd.read_csv('price_list/nbp.csv')
    df['Material'] = pd.to_numeric(df['Material'], errors='coerce')
    row = df[df['Material'] == sku]
    if row.empty:
        return None
    NBP = float(row.iloc[0]['NBP Without Tax'].replace(',', ''))
    return {
        'Material': row.iloc[0]['Material'],
        'Material Description': row.iloc[0]['Material Description'],
        'NBP': NBP,
        'Landing Price': (NBP - 15) * 1.28,
    }


if __name__ == '__main__':
    print(product_details(100227))
    results = tyre_semantic_search("Hero Splendor tyres")
    for r in results:
        print(f"\n[score={r['score']}]")
        print(r['text'][:300])