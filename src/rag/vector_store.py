"""ChromaDB-based vector store for the RAG system.

Replaces the numpy brute-force approach with ChromaDB for:
- Persistent vector storage
- Metadata filtering
- Incremental updates
- Built-in similarity search

Uses sentence-transformers for embeddings to avoid ChromaDB's ONNX
download issues.
"""
import logging
from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

CHROMADB_DIR = Path(__file__).parent.parent.parent / "data" / "rag" / "chromadb"
DEFAULT_COLLECTION = "jobpulse_jobs"
CHUNK_COLLECTION = "jobpulse_chunks"

METADATA_COLUMNS = [
    "job_id", "job_title", "company", "location", "country", "source",
    "work_mode", "seniority_level", "skills", "vacancy_url", "rag_document",
]


class SentenceTransformerEmbeddingFunction:
    """Custom embedding function using sentence-transformers."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(model_name)
        self._model_name = model_name

    def __call__(self, input: list[str]) -> list[list[float]]:
        embeddings = self.model.encode(input, show_progress_bar=False)
        return embeddings.tolist()

    def name(self) -> str:
        return f"sentence-transformers/{self._model_name}"


def _get_embedding_function():
    """Get the embedding function, trying sentence-transformers first, then ChromaDB default."""
    try:
        return SentenceTransformerEmbeddingFunction()
    except Exception as e:
        logger.warning("sentence-transformers unavailable (%s), using ChromaDB default", e)
        from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
        return DefaultEmbeddingFunction()


class JobVectorStore:
    """ChromaDB-backed vector store for job postings."""

    def __init__(
        self,
        persist_dir: Path | None = None,
        collection_name: str = DEFAULT_COLLECTION,
    ):
        self.persist_dir = Path(persist_dir) if persist_dir else CHROMADB_DIR
        self.collection_name = collection_name
        self._client = None
        self._collection = None
        self._embedding_fn = None

    def _get_client(self):
        """Lazy-load ChromaDB client."""
        if self._client is None:
            import chromadb
            self.persist_dir.mkdir(parents=True, exist_ok=True)
            self._client = chromadb.PersistentClient(path=str(self.persist_dir))
        return self._client

    def _get_embedding_function(self):
        """Get the embedding function."""
        if self._embedding_fn is None:
            self._embedding_fn = _get_embedding_function()
        return self._embedding_fn

    def _get_collection(self):
        """Get or create the ChromaDB collection."""
        if self._collection is None:
            client = self._get_client()
            ef = self._get_embedding_function()
            self._collection = client.get_or_create_collection(
                name=self.collection_name,
                embedding_function=ef,
                metadata={"hnsw:space": "cosine"},
            )
        return self._collection

    def build(
        self,
        df: pd.DataFrame,
        text_field: str = "rag_document",
        batch_size: int = 100,
    ) -> int:
        """Build the index from a DataFrame."""
        if text_field not in df.columns:
            raise ValueError(
                f"DataFrame is missing '{text_field}'. "
                f"Run NLP enrichment first."
            )

        collection = self._get_collection()
        documents = df[text_field].fillna("").tolist()

        # Prepare metadata
        ids = []
        metadatas = []
        valid_docs = []

        for i, row in df.iterrows():
            doc_id = str(row.get("job_id", f"doc_{i}"))
            if not documents[i]:
                continue

            metadata = {}
            for col in METADATA_COLUMNS:
                if col in row.index:
                    val = row[col]
                    # Handle numpy arrays and lists
                    if hasattr(val, 'tolist'):
                        val = val.tolist()
                    if isinstance(val, (list, tuple)):
                        val = ", ".join(str(v) for v in val)
                    elif isinstance(val, float) and pd.isna(val):
                        val = ""
                    # Safely check truthiness (avoid numpy array ambiguity)
                    try:
                        is_empty = not val
                    except (ValueError, TypeError):
                        is_empty = False
                    metadata[col] = str(val) if not is_empty and val is not None else ""

            ids.append(doc_id)
            metadatas.append(metadata)
            valid_docs.append(documents[i])

        # Add in batches
        for start in range(0, len(ids), batch_size):
            end = min(start + batch_size, len(ids))
            collection.add(
                ids=ids[start:end],
                documents=valid_docs[start:end],
                metadatas=metadatas[start:end],
            )
            logger.info(
                "Indexed batch %d-%d / %d",
                start, end, len(ids),
            )

        logger.info(
            "Built ChromaDB index: %d documents in '%s'",
            len(ids), self.collection_name,
        )
        return len(ids)

    def search(
        self,
        query: str,
        top_k: int = 5,
        where: dict | None = None,
        where_document: dict | None = None,
    ) -> pd.DataFrame:
        """Search the vector store."""
        collection = self._get_collection()

        query_params = {
            "query_texts": [query],
            "n_results": min(top_k, collection.count()),
        }
        if where:
            query_params["where"] = where
        if where_document:
            query_params["where_document"] = where_document

        results = collection.query(**query_params)

        # Convert to DataFrame
        records = []
        if results and results.get("ids") and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                record = {
                    "job_id": doc_id,
                    "score": 1.0 - results["distances"][0][i] if results.get("distances") else 0.0,
                }
                if results.get("metadatas") and results["metadatas"][0]:
                    metadata = results["metadatas"][0][i]
                    record.update(metadata)

                if results.get("documents") and results["documents"][0]:
                    record["rag_document"] = results["documents"][0][i]

                records.append(record)

        return pd.DataFrame(records)

    def add_documents(
        self,
        documents: list[str],
        ids: list[str],
        metadatas: list[dict] | None = None,
    ) -> int:
        """Add documents to the existing index."""
        collection = self._get_collection()
        collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
        )
        return len(ids)

    def delete(self, ids: list[str]) -> None:
        """Delete documents by ID."""
        collection = self._get_collection()
        collection.delete(ids=ids)

    def count(self) -> int:
        """Return the number of documents in the index."""
        return self._get_collection().count()

    def exists(self) -> bool:
        """Check if the index has any documents."""
        try:
            return self.count() > 0
        except Exception:
            return False

    def clear(self) -> None:
        """Clear all documents from the index."""
        client = self._get_client()
        try:
            client.delete_collection(self.collection_name)
            self._collection = None
            logger.info("Cleared collection '%s'", self.collection_name)
        except Exception:
            pass

    def get_metadata_stats(self) -> dict[str, Any]:
        """Get statistics about the stored data."""
        collection = self._get_collection()
        total = collection.count()

        if total == 0:
            return {"total_documents": 0}

        # Get all documents to compute accurate stats
        all_data = collection.get(include=["metadatas"])
        countries = set()
        work_modes = set()
        seniority_levels = set()

        if all_data.get("metadatas"):
            for meta in all_data["metadatas"]:
                if meta.get("country"):
                    countries.add(meta["country"])
                if meta.get("work_mode"):
                    work_modes.add(meta["work_mode"])
                if meta.get("seniority_level"):
                    seniority_levels.add(meta["seniority_level"])

        return {
            "total_documents": total,
            "countries": sorted(countries),
            "work_modes": sorted(work_modes),
            "seniority_levels": sorted(seniority_levels),
        }
