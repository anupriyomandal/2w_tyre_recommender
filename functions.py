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


_sku_position_map: dict[int, str] | None = None


def _load_sku_position_map() -> dict[int, str]:
    """Build SKU -> position ('Front', 'Rear', 'Front/Rear') from vehicle mapping CSV."""
    global _sku_position_map
    if _sku_position_map is not None:
        return _sku_position_map

    vdf = pd.read_csv(
        'data/mcy-vehicle-sku-mapping-v18-14.04.2026.csv', encoding='utf-8-sig'
    )
    vdf['type'] = vdf['type'].str.strip().replace('Font', 'Front')

    alt_cols = ['upsize-sku', 'alternate-sku1', 'alternate-sku2',
                'alternate-sku3', 'Unnamed: 11', 'Unnamed: 12']
    positions: dict[int, set] = {}

    for _, row in vdf.iterrows():
        pos = str(row['type']).strip()
        for col in ['recommended-sku'] + alt_cols:
            try:
                val = row.get(col)
                f = float(str(val).strip())
                if not np.isnan(f):
                    sku = int(f)
                    positions.setdefault(sku, set()).add(pos)
            except (ValueError, TypeError):
                pass

    _sku_position_map = {
        sku: '/'.join(sorted(pos_set))
        for sku, pos_set in positions.items()
    }
    return _sku_position_map


def tyre_size_search(size: str) -> list[dict]:
    """Return all CEAT tyre SKUs matching a given size, labelled Front, Rear, or Front/Rear."""
    price_df = pd.read_csv('price_list/nbp.csv')
    price_df['Material'] = pd.to_numeric(price_df['Material'], errors='coerce')
    size_clean = size.strip()
    mask = (
        price_df['Material Description'].str.contains(size_clean, case=False, na=False, regex=False) &
        ~price_df['Material Description'].str.upper().str.startswith('TUBE')
    )
    matches = price_df[mask].dropna(subset=['Material'])
    pos_map = _load_sku_position_map()

    results = []
    for _, row in matches.iterrows():
        sku = int(row['Material'])
        desc = str(row['Material Description'])
        nbp = float(str(row['NBP Without Tax']).replace(',', ''))

        # Look up position from vehicle mapping; fall back to name heuristic
        position = pos_map.get(sku)
        if not position:
            position = 'Front' if ' F ' in f' {desc} ' else 'Rear'

        results.append({
            'SKU': sku,
            'Description': desc,
            'Position': position,
            'Landing Price': int(round((nbp - 15) * 1.28)),
        })

    # Sort: Front first, then Front/Rear, then Rear
    order = {'Front': 0, 'Front/Rear': 1, 'Rear': 2}
    results.sort(key=lambda r: order.get(r['Position'], 3))
    return results


if __name__ == '__main__':
    print(product_details(100227))
    results = tyre_semantic_search("Hero Splendor tyres")
    for r in results:
        print(f"\n[score={r['score']}]")
        print(r['text'][:300])