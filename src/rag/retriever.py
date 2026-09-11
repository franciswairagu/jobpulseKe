"""ChromaDB-backed retriever for the RAG system.

Provides semantic retrieval over job postings with metadata filtering,
confidence scoring, and context formatting for LLM generation.
"""
import logging
from pathlib import Path
from typing import Any, Optional

import pandas as pd

from src.config import NLP_DATA_DIR, RAG_DATA_DIR
from src.rag.vector_store import JobVectorStore
from src.rag.prompts import format_retrieved_context

logger = logging.getLogger(__name__)

LOW_CONFIDENCE_THRESHOLD = 0.15


class JobPulseRAG:
    """High-level retriever: build/load ChromaDB index and query it."""

    def __init__(self, persist_dir: Path | None = None):
        self.store = JobVectorStore(persist_dir=persist_dir or RAG_DATA_DIR)

    def build(
        self,
        nlp_parquet: Path | None = None,
        text_field: str = "rag_document",
        save: bool = True,
    ) -> "JobPulseRAG":
        """Build the index from the enriched NLP dataset."""
        from src.nlp.nlpv2 import latest_nlp_output

        if nlp_parquet is None:
            nlp_parquet = latest_nlp_output()
        if nlp_parquet is None or not Path(nlp_parquet).exists():
            raise FileNotFoundError(
                f"No NLP output found in {NLP_DATA_DIR}. "
                f"Run src/nlp/nlpv2.py first."
            )

        logger.info("Building RAG index from %s", nlp_parquet)
        df = pd.read_parquet(nlp_parquet)
        self.store.build(df, text_field=text_field)
        return self

    def load(self) -> "JobPulseRAG":
        """Load existing index (no-op for ChromaDB, it auto-loads)."""
        if not self.store.exists():
            raise FileNotFoundError("No index found. Run build() first.")
        return self

    def ensure_ready(self) -> "JobPulseRAG":
        """Load if exists, otherwise build."""
        if self.store.exists():
            return self.load()
        return self.build()

    def query(
        self,
        text: str,
        top_k: int = 5,
        where: dict | None = None,
    ) -> pd.DataFrame:
        """Query the index with semantic search."""
        if not text or not text.strip():
            return pd.DataFrame()

        return self.store.search(text, top_k=top_k, where=where)

    def query_with_filters(
        self,
        text: str,
        top_k: int = 5,
        country: str | None = None,
        work_mode: str | None = None,
        seniority_level: str | None = None,
    ) -> pd.DataFrame:
        """Query with metadata filters."""
        where_conditions = {}
        if country:
            where_conditions["country"] = country
        if work_mode:
            where_conditions["work_mode"] = work_mode
        if seniority_level:
            where_conditions["seniority_level"] = seniority_level

        where = where_conditions if where_conditions else None
        return self.query(text, top_k=top_k, where=where)

    @staticmethod
    def has_strong_matches(
        results: pd.DataFrame,
        threshold: float = LOW_CONFIDENCE_THRESHOLD,
    ) -> bool:
        """Check if top result clears the confidence bar."""
        if results.empty:
            return False
        return bool(results["score"].iloc[0] >= threshold)

    @staticmethod
    def format_context(results: pd.DataFrame) -> str:
        """Format results into context block for LLM."""
        context_list = []
        for _, row in results.iterrows():
            entry = {
                "text": row.get("rag_document", ""),
                "score": row.get("score", 0.0),
                "metadata": {
                    "job_id": row.get("job_id", ""),
                    "job_title": row.get("job_title", ""),
                    "company": row.get("company", ""),
                    "location": row.get("location", ""),
                    "country": row.get("country", ""),
                    "work_mode": row.get("work_mode", ""),
                    "seniority_level": row.get("seniority_level", ""),
                    "skills": row.get("skills", []),
                },
            }
            context_list.append(entry)

        return format_retrieved_context(context_list)
