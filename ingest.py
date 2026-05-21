import os
import json
from pathlib import Path

import numpy as np
import pandas as pd
import faiss
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

DATA_DIR = Path("data")
VECTOR_STORE_DIR = Path("vector_store")
EMBED_MODEL = "text-embedding-3-small"
EMBED_DIM = 1536
BATCH_SIZE = 100

# All columns that may contain alternate SKUs
ALT_SKU_COLS = ["alternate-sku1", "alternate-sku2", "alternate-sku3", "Unnamed: 11", "Unnamed: 12"]

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def _safe_int(val) -> int | None:
    try:
        f = float(str(val).strip())
        return int(f) if not np.isnan(f) else None
    except (ValueError, TypeError):
        return None


def build_variant_docs(csv_path: Path) -> list[dict]:
    """One document per (brand, model, variant) combining all tyre positions."""
    df = pd.read_csv(csv_path, encoding="utf-8-sig")

    # Normalize typo: "Font" → "Front"
    df["type"] = df["type"].str.strip().replace("Font", "Front")

    docs = []
    group_keys = ["category", "vehicle-brand", "vehicle-model", "vehicle-variant"]

    for keys, group in df.groupby(group_keys, sort=False):
        category, brand, model, variant = keys

        lines = [f"{brand} {model} {variant}"]
        rows_data = []

        for _, row in group.iterrows():
            position = str(row["type"]).strip()
            sku = _safe_int(row.get("recommended-sku"))
            desc = str(row.get("sku-desc.", "")).strip()

            alts = [_safe_int(row.get(c)) for c in ALT_SKU_COLS]
            alts = [a for a in alts if a is not None]

            line = f"{position} Tyre — SKU {sku}: {desc}"
            if alts:
                line += f" | Alt SKUs: {', '.join(str(a) for a in alts)}"
            lines.append(line)

            rows_data.append({
                "type": position,
                "recommended_sku": sku,
                "sku_desc": desc,
                "alt_skus": alts,
            })

        text = "\n".join(lines)
        docs.append({
            "source": str(csv_path.relative_to(DATA_DIR)),
            "chunk_index": len(docs),
            "text": text,
            "category": str(category),
            "brand": str(brand),
            "model": str(model),
            "variant": str(variant),
            "rows": rows_data,
        })

    return docs


def embed_texts(texts: list[str]) -> np.ndarray:
    embeddings = []
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i: i + BATCH_SIZE]
        response = client.embeddings.create(model=EMBED_MODEL, input=batch)
        batch_vecs = [item.embedding for item in sorted(response.data, key=lambda x: x.index)]
        embeddings.extend(batch_vecs)
        print(f"  embedded {min(i + BATCH_SIZE, len(texts))}/{len(texts)} variants")
    return np.array(embeddings, dtype=np.float32)


def _normalize(vectors: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    return vectors / np.where(norms == 0, 1, norms)


def ingest():
    VECTOR_STORE_DIR.mkdir(exist_ok=True)

    csv_files = sorted(f for f in DATA_DIR.rglob("*.csv") if f.is_file())
    if not csv_files:
        print(f"No CSV files found in {DATA_DIR}/")
        return

    print(f"Found {len(csv_files)} CSV file(s)")
    all_docs: list[dict] = []

    for csv_path in csv_files:
        print(f"\nLoading {csv_path.relative_to(DATA_DIR)} ...")
        docs = build_variant_docs(csv_path)
        print(f"  -> {len(docs)} vehicle variants")
        all_docs.extend(docs)

    texts = [d["text"] for d in all_docs]
    print(f"\nEmbedding {len(texts)} variant document(s) via {EMBED_MODEL} ...")
    embeddings = embed_texts(texts)

    print("\nBuilding FAISS index ...")
    index = faiss.IndexFlatIP(EMBED_DIM)
    index.add(_normalize(embeddings))

    faiss.write_index(index, str(VECTOR_STORE_DIR / "index.faiss"))
    (VECTOR_STORE_DIR / "metadata.json").write_text(
        json.dumps(all_docs, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"\nDone — {index.ntotal} vectors saved to {VECTOR_STORE_DIR}/")


if __name__ == "__main__":
    ingest()
