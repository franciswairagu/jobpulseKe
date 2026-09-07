"""
Persistent vector store for the RAG system.

Deliberately a small numpy-based store rather than chromadb: with ~10k
jobs, brute-force cosine similarity (a single matrix-vector product) is
sub-millisecond and this avoids chromadb's own dependency/startup weight
for what is, at this scale, a solved problem. If the dataset grows into
the hundreds of thousands+ of records, swap this class's `search()` for
a chromadb/FAISS-backed one — the JobPulseRAG interface in retriever.py
wouldn't need to change.

Persists under data/rag/:
  - vectors.npz (sparse, TF-IDF) or vectors.npy (dense, sentence-
    transformer) — whichever backend built the index
  - metadata.parquet   one row per doc: job_id, job_title, company,
    location, country, source, vacancy_url, rag_document (for display)
  - embedder.pkl   the fitted embedder (see embeddings.py), so queries
    are embedded the same way the corpus was
"""
import logging
from pathlib import Path
from typing import List, Optional, Union

import numpy as np
import pandas as pd
import scipy.sparse as sp

from src.rag.embeddings import BaseEmbedder, get_embedder, load_embedder
from src.rag.validation import validate_query

logger = logging.getLogger(__name__)

# TF-IDF vectors stay sparse (see embeddings.py) and are saved as .npz;
# sentence-transformer vectors are dense and saved as .npy. Exactly one
# of the two exists in an index dir at a time.
VECTORS_DENSE_FILENAME = "vectors.npy"
VECTORS_SPARSE_FILENAME = "vectors.npz"
METADATA_FILENAME = "metadata.parquet"
EMBEDDER_FILENAME = "embedder.pkl"

# Columns kept alongside each vector for display/filtering at query time —
# everything else in the enriched NLP dataset is available by re-joining
# on job_id if needed, but doesn't need to ride along in the index itself.
METADATA_COLUMNS = [
    "job_id", "job_title", "company", "location", "country", "source",
    "work_mode", "seniority_level", "skills", "vacancy_url", "rag_document",
]


class JobVectorStore:
    """Build, persist, and search a vector index over job postings."""

    def __init__(self, index_dir: Path):
        self.index_dir = Path(index_dir)
        self.embedder: Optional[BaseEmbedder] = None
        self.vectors: Optional[np.ndarray] = None
        self.metadata: Optional[pd.DataFrame] = None

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------
    def build(self, df: pd.DataFrame, embedder_prefer: str = "auto") -> None:
        """Build the index from an enriched NLP dataframe (must have a
        `rag_document` column — see src/nlp/nlpv2.py)."""
        if "rag_document" not in df.columns:
            raise ValueError(
                "DataFrame is missing 'rag_document' — build it with "
                "src.nlp.nlpv2.run_nlp_extraction_v2() first."
            )

        documents = df["rag_document"].fillna("").tolist()
        logger.info("Fitting embedder on %d documents...", len(documents))

        self.embedder = get_embedder(prefer=embedder_prefer)
        self.embedder.fit(documents)
        self.vectors = self.embedder.embed(documents)

        available_cols = [c for c in METADATA_COLUMNS if c in df.columns]
        self.metadata = df[available_cols].reset_index(drop=True)

        logger.info(
            "Built index: %d vectors, dim=%d, backend=%s",
            self.vectors.shape[0], self.vectors.shape[1], self.embedder.name,
        )

    # ------------------------------------------------------------------
    # Persist / load
    # ------------------------------------------------------------------
    def save(self) -> None:
        if self.vectors is None or self.metadata is None or self.embedder is None:
            raise RuntimeError("Nothing to save — call build() first")
        self.index_dir.mkdir(parents=True, exist_ok=True)

        if sp.issparse(self.vectors):
            sp.save_npz(self.index_dir / VECTORS_SPARSE_FILENAME, self.vectors)
            # Remove a stale dense file from a previous build with a
            # different backend, so load() doesn't pick up the wrong one.
            (self.index_dir / VECTORS_DENSE_FILENAME).unlink(missing_ok=True)
        else:
            np.save(self.index_dir / VECTORS_DENSE_FILENAME, self.vectors)
            (self.index_dir / VECTORS_SPARSE_FILENAME).unlink(missing_ok=True)

        self.metadata.to_parquet(self.index_dir / METADATA_FILENAME, index=False)
        self.embedder.save(self.index_dir / EMBEDDER_FILENAME)
        logger.info("Saved index to %s", self.index_dir)

    def load(self) -> None:
        sparse_path = self.index_dir / VECTORS_SPARSE_FILENAME
        dense_path = self.index_dir / VECTORS_DENSE_FILENAME
        metadata_path = self.index_dir / METADATA_FILENAME
        embedder_path = self.index_dir / EMBEDDER_FILENAME

        if not ((sparse_path.exists() or dense_path.exists())
                and metadata_path.exists() and embedder_path.exists()):
            raise FileNotFoundError(
                f"No saved index found in {self.index_dir}. "
                f"Run scripts/build_rag_index.py first."
            )

        if sparse_path.exists():
            self.vectors = sp.load_npz(sparse_path)
        else:
            self.vectors = np.load(dense_path)

        self.metadata = pd.read_parquet(metadata_path)
        self.embedder = load_embedder(embedder_path)
        logger.info(
            "Loaded index: %d vectors, backend=%s", self.vectors.shape[0], self.embedder.name,
        )

    def exists(self) -> bool:
        has_vectors = (self.index_dir / VECTORS_SPARSE_FILENAME).exists() or \
            (self.index_dir / VECTORS_DENSE_FILENAME).exists()
        return has_vectors and all(
            (self.index_dir / f).exists()
            for f in (METADATA_FILENAME, EMBEDDER_FILENAME)
        )

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------
    def search(self, query: str, top_k: int = 5) -> pd.DataFrame:
        if self.vectors is None or self.metadata is None or self.embedder is None:
            raise RuntimeError("Index not loaded — call load() or build() first")

        # Raises QueryValidationError with a user-facing message for bad
        # input (empty, wrong type, no real content); silently clamps
        # top_k into a sane range rather than erroring on that one.
        query, top_k = validate_query(query, top_k)

        query_vector = self.embedder.embed([query])
        # Vectors are L2-normalized at embed time, so a dot product IS
        # cosine similarity. Sparse (TF-IDF) @ dense query -> dense 1D
        # scores array either way.
        if sp.issparse(query_vector):
            query_vector = query_vector.toarray()
        query_vector = np.asarray(query_vector).reshape(-1)

        scores = self.vectors @ query_vector
        scores = np.asarray(scores).reshape(-1)

        top_k = min(top_k, len(scores))
        top_idx = np.argpartition(-scores, top_k - 1)[:top_k]
        top_idx = top_idx[np.argsort(-scores[top_idx])]

        results = self.metadata.iloc[top_idx].copy()
        results["score"] = scores[top_idx]
        return results.reset_index(drop=True)
