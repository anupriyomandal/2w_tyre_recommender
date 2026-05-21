import numpy as np
import faiss
from dataclasses import dataclass
from typing import Any


@dataclass
class SearchResult:
    index: int
    score: float
    metadata: Any = None


def _normalize(vectors: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1, norms)  # avoid division by zero
    return vectors / norms


def build_index(vectors: np.ndarray) -> faiss.IndexFlatIP:
    """Build a FAISS inner-product index from float32 vectors.

    Vectors are L2-normalized so inner product equals cosine similarity.
    """
    vectors = np.array(vectors, dtype=np.float32)
    if vectors.ndim == 1:
        vectors = vectors[np.newaxis, :]
    normalized = _normalize(vectors)
    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(normalized)
    return index


def semantic_search(
    query_vector: np.ndarray,
    index: faiss.IndexFlatIP,
    top_k: int = 5,
    metadata: list[Any] | None = None,
) -> list[SearchResult]:
    """Search a FAISS index for the top-k most similar vectors.

    Args:
        query_vector: 1-D or 2-D float array of shape (dim,) or (1, dim).
        index: FAISS index built with build_index().
        top_k: Number of results to return.
        metadata: Optional list aligned with the indexed vectors; values are
                  attached to each SearchResult.

    Returns:
        List of SearchResult sorted by descending cosine similarity score.
    """
    query = np.array(query_vector, dtype=np.float32)
    if query.ndim == 1:
        query = query[np.newaxis, :]
    query = _normalize(query)

    top_k = min(top_k, index.ntotal)
    scores, indices = index.search(query, top_k)

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:
            continue
        results.append(
            SearchResult(
                index=int(idx),
                score=float(score),
                metadata=metadata[idx] if metadata is not None else None,
            )
        )
    return results


# ---------------------------------------------------------------------------
# Quick smoke test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    rng = np.random.default_rng(42)
    dim = 8
    corpus = rng.standard_normal((20, dim)).astype(np.float32)
    labels = [f"doc_{i}" for i in range(20)]

    idx = build_index(corpus)

    query = corpus[3] + rng.standard_normal(dim).astype(np.float32) * 0.1
    results = semantic_search(query, idx, top_k=3, metadata=labels)

    print("Top results for query (perturbed doc_3):")
    for r in results:
        print(f"  [{r.metadata}] score={r.score:.4f}")
