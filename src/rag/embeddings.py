"""
Embedding backends for the RAG system.

Two backends, same interface (fit/embed):

  - SentenceTransformerEmbedder: real semantic embeddings (all-MiniLM-L6-v2).
    Needs network access on first run to download model weights from
    huggingface.co, and the `sentence-transformers` package (already in
    requirements.txt).
  - TfidfEmbedder: scikit-learn TF-IDF vectors. No download, no network,
    works instantly anywhere scikit-learn is installed (also already in
    requirements.txt) — keyword-level rather than semantic similarity,
    but a solid, honest fallback.

get_embedder(prefer="auto") tries sentence-transformers first and falls
back to TF-IDF automatically (e.g. no internet access, or the package
isn't installed) — so build_rag_index.py and query_rag.py work out of
the box in any environment, and upgrade to real semantic search for free
the moment sentence-transformers can actually reach huggingface.co.
"""
import logging
import pickle
from pathlib import Path
from typing import List, Union

import numpy as np
import scipy.sparse as sp

logger = logging.getLogger(__name__)

DEFAULT_ST_MODEL = "all-MiniLM-L6-v2"


class BaseEmbedder:
    """Common interface every embedding backend implements."""

    name: str = "base"

    def fit(self, documents: List[str]) -> None:
        """Fit any vocabulary/model needed on the corpus (no-op for
        pretrained models like sentence-transformers)."""
        raise NotImplementedError

    def embed(self, texts: List[str]) -> Union[np.ndarray, sp.csr_matrix]:
        """Return an (n_texts, dim) embedding matrix — dense for
        sentence-transformers, sparse (csr_matrix) for TF-IDF."""
        raise NotImplementedError

    def save(self, path: Path) -> None:
        raise NotImplementedError

    @classmethod
    def load(cls, path: Path) -> "BaseEmbedder":
        raise NotImplementedError


class SentenceTransformerEmbedder(BaseEmbedder):
    """Real semantic embeddings via sentence-transformers."""

    name = "sentence-transformer"

    def __init__(self, model_name: str = DEFAULT_ST_MODEL):
        from sentence_transformers import SentenceTransformer  # deferred import
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)

    def fit(self, documents: List[str]) -> None:
        pass  # pretrained model, nothing to fit

    def embed(self, texts: List[str]) -> np.ndarray:
        return np.asarray(
            self.model.encode(texts, show_progress_bar=False, normalize_embeddings=True),
            dtype=np.float32,
        )

    def save(self, path: Path) -> None:
        # Only the model name needs persisting — weights are re-downloaded
        # (and cached by sentence-transformers itself) on load.
        with open(path, "wb") as f:
            pickle.dump({"backend": self.name, "model_name": self.model_name}, f)

    @classmethod
    def load(cls, path: Path) -> "SentenceTransformerEmbedder":
        with open(path, "rb") as f:
            meta = pickle.load(f)
        return cls(model_name=meta["model_name"])


class TfidfEmbedder(BaseEmbedder):
    """Offline fallback: TF-IDF vectors, kept SPARSE throughout.

    TfidfVectorizer already L2-normalizes rows by default, so a sparse
    dot product IS cosine similarity — same contract as the dense
    sentence-transformer backend. Important: never call .toarray() on
    the full corpus matrix here — with max_features=20000 over ~10k
    docs that's an 800MB+ dense float32 array for what is, sparsely,
    a few MB. embed() returns a scipy.sparse.csr_matrix; JobVectorStore
    knows how to store/search either sparse or dense.
    """

    name = "tfidf"

    def __init__(self, max_features: int = 5000):
        from sklearn.feature_extraction.text import TfidfVectorizer  # deferred import
        self.max_features = max_features
        self.vectorizer = TfidfVectorizer(
            max_features=max_features,
            stop_words="english",
            ngram_range=(1, 2),
        )
        self._fitted = False

    def fit(self, documents: List[str]) -> None:
        self.vectorizer.fit(documents)
        self._fitted = True

    def embed(self, texts: List[str]) -> sp.csr_matrix:
        if not self._fitted:
            raise RuntimeError("TfidfEmbedder.fit() must be called before embed()")
        return self.vectorizer.transform(texts).astype(np.float32)  # already L2-normalized

    def save(self, path: Path) -> None:
        with open(path, "wb") as f:
            pickle.dump({"backend": self.name, "vectorizer": self.vectorizer}, f)

    @classmethod
    def load(cls, path: Path) -> "TfidfEmbedder":
        with open(path, "rb") as f:
            meta = pickle.load(f)
        obj = cls.__new__(cls)
        obj.vectorizer = meta["vectorizer"]
        obj.max_features = obj.vectorizer.max_features
        obj._fitted = True
        return obj


def get_embedder(prefer: str = "auto") -> BaseEmbedder:
    """Return a ready-to-use embedder.

    prefer: "auto" (try sentence-transformers, fall back to TF-IDF),
            "sentence-transformer" (force, raises if unavailable),
            "tfidf" (force TF-IDF).
    """
    if prefer == "tfidf":
        return TfidfEmbedder()

    if prefer == "sentence-transformer":
        return SentenceTransformerEmbedder()

    # auto
    try:
        embedder = SentenceTransformerEmbedder()
        # Cheap smoke test — sentence-transformers only fails at .encode()
        # time if the model weights couldn't be downloaded/cached.
        embedder.embed(["smoke test"])
        logger.info("Using sentence-transformer embeddings (%s)", DEFAULT_ST_MODEL)
        return embedder
    except Exception as e:
        logger.warning(
            "sentence-transformers unavailable (%s: %s) — falling back to "
            "TF-IDF embeddings. Keyword search will still work; semantic "
            "search will not until this environment has model access.",
            type(e).__name__, str(e)[:200],
        )
        return TfidfEmbedder()


def load_embedder(path: Path) -> BaseEmbedder:
    """Load whichever backend was persisted, without the caller needing
    to know in advance which one it was."""
    with open(path, "rb") as f:
        meta = pickle.load(f)
    backend = meta.get("backend")
    if backend == "sentence-transformer":
        return SentenceTransformerEmbedder.load(path)
    elif backend == "tfidf":
        return TfidfEmbedder.load(path)
    raise ValueError(f"Unknown embedder backend in {path}: {backend}")
