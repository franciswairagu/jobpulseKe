"""
JobPulseRAG — retrieval-augmented search over enriched job postings.

Retrieval side only (embed corpus -> index -> similarity search -> ranked
job results + an assembled context block). Generation (feeding that
context to an LLM to produce a natural-language answer) is a thin final
step deliberately left as a hook — `format_context()` below returns
exactly the block you'd drop into a prompt — rather than hardcoding a
specific model/API choice into the pipeline.

Usage:
    from src.rag.retriever import JobPulseRAG

    rag = JobPulseRAG()
    rag.load()                                   # or rag.build() the first time
    results = rag.query("remote python developer in Kenya", top_k=5)
    print(rag.format_context(results))
"""
import logging
from pathlib import Path
from typing import Optional

import pandas as pd

from src.config import NLP_DATA_DIR, RAG_DATA_DIR
from src.rag.vector_store import JobVectorStore
from src.rag.validation import QueryValidationError
from src.nlp.nlpv2 import latest_nlp_output

logger = logging.getLogger(__name__)

# Below this cosine-similarity score, results are more likely noise than
# genuine matches (e.g. a query about a role/skill nothing in the corpus
# covers). Not an error — still returned — but callers should tell the
# user these are weak matches rather than presenting them as confident
# hits. Threshold is conservative for TF-IDF (sparse keyword overlap
# scores lower than dense semantic similarity even for good matches).
LOW_CONFIDENCE_THRESHOLD = 0.15


class JobPulseRAG:
    """High-level entry point: build/load a vector index over the NLP
    stage's enriched jobs and query it."""

    def __init__(self, index_dir: Path = RAG_DATA_DIR):
        self.store = JobVectorStore(index_dir)

    def build(
        self,
        nlp_parquet: Optional[Path] = None,
        embedder_prefer: str = "auto",
        save: bool = True,
    ) -> "JobPulseRAG":
        """Build the index from the enriched NLP dataset and persist it."""
        if nlp_parquet is None:
            nlp_parquet = latest_nlp_output()
        if nlp_parquet is None or not Path(nlp_parquet).exists():
            raise FileNotFoundError(
                f"No NLP output found in {NLP_DATA_DIR}. "
                f"Run src/nlp/nlpv2.py (or scripts/run_nlp_extraction.py) first."
            )

        logger.info("Building RAG index from %s", nlp_parquet)
        df = pd.read_parquet(nlp_parquet)
        self.store.build(df, embedder_prefer=embedder_prefer)
        if save:
            self.store.save()
        return self

    def load(self) -> "JobPulseRAG":
        """Load a previously built + saved index."""
        self.store.load()
        return self

    def ensure_ready(self, embedder_prefer: str = "auto") -> "JobPulseRAG":
        """Load the persisted index if one exists, otherwise build it
        fresh from the latest NLP output. Convenience for callers who
        don't care which of the two just happened."""
        if self.store.exists():
            return self.load()
        return self.build(embedder_prefer=embedder_prefer)

    def query(self, text: str, top_k: int = 5) -> pd.DataFrame:
        """Return the top_k most relevant job postings for a free-text
        query, ranked by similarity score (highest first).

        Raises QueryValidationError (a ValueError subclass) for input
        that can't be searched at all — empty, wrong type, or no real
        text content. See src/rag/validation.py for exact rules.
        """
        return self.store.search(text, top_k=top_k)

    @staticmethod
    def has_strong_matches(results: pd.DataFrame, threshold: float = LOW_CONFIDENCE_THRESHOLD) -> bool:
        """True if the top result clears the low-confidence bar. A valid,
        well-formed query can still come back empty-handed if nothing in
        the corpus is actually relevant — this is how a caller tells that
        apart from a genuine match."""
        if results.empty:
            return False
        return bool(results["score"].iloc[0] >= threshold)

    @staticmethod
    def format_context(results: pd.DataFrame) -> str:
        """Assemble retrieved jobs into a single context block, ready to
        drop into an LLM prompt for generation (e.g. "Given these job
        postings, answer the user's question: ...")."""
        blocks = []
        for i, row in results.iterrows():
            url = row.get("vacancy_url")
            url = url if isinstance(url, str) and url.strip() else "N/A"
            blocks.append(
                f"[Result {i + 1} | score={row['score']:.3f}]\n"
                f"{row['rag_document']}\n"
                f"Apply: {url}"
            )
        return "\n\n---\n\n".join(blocks)
