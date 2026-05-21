import os
import json
from pathlib import Path

import numpy as np
import faiss
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

DATA_DIR = Path("data")
VECTOR_STORE_DIR = Path("vector_store")

EMBED_MODEL = "text-embedding-3-small"
EMBED_DIM = 1536
CHUNK_SIZE = 1000   # characters
CHUNK_OVERLAP = 200
BATCH_SIZE = 100    # max embeddings per OpenAI request

SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf", ".docx", ".csv"}

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# ---------------------------------------------------------------------------
# Document loading
# ---------------------------------------------------------------------------

def _load_txt(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _load_pdf(path: Path) -> str:
    import pypdf
    reader = pypdf.PdfReader(str(path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _load_docx(path: Path) -> str:
    from docx import Document
    doc = Document(str(path))
    return "\n".join(p.text for p in doc.paragraphs)


def load_document(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in (".txt", ".md", ".csv"):
        return _load_txt(path)
    if ext == ".pdf":
        return _load_pdf(path)
    if ext == ".docx":
        return _load_docx(path)
    return ""


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------

def chunk_text(text: str) -> list[str]:
    text = text.strip()
    chunks, start = [], 0
    while start < len(text):
        chunk = text[start : start + CHUNK_SIZE].strip()
        if chunk:
            chunks.append(chunk)
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks


# ---------------------------------------------------------------------------
# Embedding
# ---------------------------------------------------------------------------

def embed_texts(texts: list[str]) -> np.ndarray:
    embeddings = []
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i : i + BATCH_SIZE]
        response = client.embeddings.create(model=EMBED_MODEL, input=batch)
        batch_vecs = [item.embedding for item in sorted(response.data, key=lambda x: x.index)]
        embeddings.extend(batch_vecs)
        print(f"  embedded {min(i + BATCH_SIZE, len(texts))}/{len(texts)} chunks")
    return np.array(embeddings, dtype=np.float32)


def _normalize(vectors: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1, norms)
    return vectors / norms


# ---------------------------------------------------------------------------
# Main ingest pipeline
# ---------------------------------------------------------------------------

def ingest():
    VECTOR_STORE_DIR.mkdir(exist_ok=True)

    files = sorted(
        f for f in DATA_DIR.rglob("*")
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
    )

    if not files:
        print(f"No supported files found in {DATA_DIR}/  (supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))})")
        return

    print(f"Found {len(files)} file(s) in {DATA_DIR}/")

    all_chunks: list[str] = []
    all_metadata: list[dict] = []

    for file in files:
        print(f"\nLoading  {file.relative_to(DATA_DIR)}")
        text = load_document(file)
        if not text.strip():
            print("  [skip] no text extracted")
            continue
        chunks = chunk_text(text)
        print(f"  → {len(chunks)} chunk(s)")
        for i, chunk in enumerate(chunks):
            all_chunks.append(chunk)
            all_metadata.append({
                "source": str(file.relative_to(DATA_DIR)),
                "chunk_index": i,
                "text": chunk,
            })

    if not all_chunks:
        print("\nNo text content extracted from any file.")
        return

    print(f"\nEmbedding {len(all_chunks)} chunk(s) via {EMBED_MODEL} ...")
    embeddings = embed_texts(all_chunks)

    print("\nBuilding FAISS index ...")
    index = faiss.IndexFlatIP(EMBED_DIM)
    index.add(_normalize(embeddings))

    index_path = VECTOR_STORE_DIR / "index.faiss"
    meta_path = VECTOR_STORE_DIR / "metadata.json"

    faiss.write_index(index, str(index_path))
    meta_path.write_text(
        json.dumps(all_metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"\nDone — {index.ntotal} vector(s) saved to {VECTOR_STORE_DIR}/")
    print(f"  {index_path}")
    print(f"  {meta_path}")


if __name__ == "__main__":
    ingest()
