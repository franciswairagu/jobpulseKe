"""RAG Retrieval evaluation — Precision@k, Recall@k, MRR with auto-generated relevance."""

import logging
from typing import Any, Dict, List, Optional

import pandas as pd

from src.config import RAG_DATA_DIR
from src.rag.retriever import JobPulseRAG

logger = logging.getLogger(__name__)

# Test queries with auto-generated keyword-based relevance criteria
TEST_QUERIES = [
    {"query": "python developer", "relevant_keywords": ["python"]},
    {"query": "react frontend developer", "relevant_keywords": ["react", "frontend"]},
    {"query": "remote jobs in Kenya", "relevant_keywords": ["kenya", "remote"]},
    {"query": "aws cloud engineer", "relevant_keywords": ["aws", "cloud"]},
    {"query": "data scientist machine learning", "relevant_keywords": ["data scien", "machine learn", "ml"]},
    {"query": "devops kubernetes docker", "relevant_keywords": ["kubernetes", "docker", "devops"]},
    {"query": "junior entry level developer", "relevant_keywords": ["junior", "entry"]},
    {"query": "senior software engineer", "relevant_keywords": ["senior"]},
    {"query": "nigeria tech jobs", "relevant_keywords": ["nigeria"]},
    {"query": "sql database developer", "relevant_keywords": ["sql", "database"]},
    {"query": "full stack javascript", "relevant_keywords": ["full stack", "javascript"]},
    {"query": "terraform infrastructure", "relevant_keywords": ["terraform", "infrastructure"]},
    {"query": "django python backend", "relevant_keywords": ["django", "python"]},
    {"query": "south africa remote work", "relevant_keywords": ["south africa", "remote"]},
    {"query": "golang microservices", "relevant_keywords": ["go", "golang", "microservices"]},
]


def _auto_label_relevance(results: pd.DataFrame, relevant_keywords: List[str]) -> List[int]:
    """Auto-generate binary relevance labels for retrieved results.

    A document is considered relevant if any of the keywords appear in
    its rag_document (case-insensitive).
    """
    labels = []
    for _, row in results.iterrows():
        doc = str(row.get("rag_document", "")).lower()
        is_relevant = any(kw in doc for kw in relevant_keywords)
        labels.append(1 if is_relevant else 0)
    return labels


def _precision_at_k(relevant: List[int], k: int) -> float:
    """Precision at k: relevant items in top-k / k."""
    top_k = relevant[:k]
    return sum(top_k) / k if k > 0 else 0.0


def _recall_at_k(relevant: List[int], k: int, total_relevant: int) -> float:
    """Recall at k: relevant items in top-k / total relevant in full result set."""
    if total_relevant == 0:
        return 0.0
    top_k = relevant[:k]
    return sum(top_k) / total_relevant


def _mrr(relevant: List[int]) -> float:
    """Mean Reciprocal Rank: 1/rank of first relevant result."""
    for i, rel in enumerate(relevant):
        if rel == 1:
            return 1.0 / (i + 1)
    return 0.0


def evaluate_rag_retrieval(
    top_k: int = 10,
    nlp_parquet: Optional[str] = None,
) -> Dict[str, Any]:
    """Evaluate RAG retrieval quality with auto-generated relevance labels.

    For each test query:
      1. Query the RAG system
      2. Auto-label relevance using keyword matching
      3. Compute Precision@k, Recall@k, MRR

    Returns aggregate metrics + per-query detail.
    """
    try:
        rag = JobPulseRAG()
        if not rag.store.exists():
            logger.warning("RAG index not found — attempting to build")
            rag.build()
        else:
            rag.load()
    except Exception as e:
        logger.error("Failed to load RAG index: %s", e)
        return {
            "model": "rag_retrieval",
            "status": "error",
            "error": str(e),
        }

    per_query = []
    total_p3 = total_p5 = total_r5 = total_mrr = 0
    n_queries = 0
    low_confidence_count = 0

    for query_spec in TEST_QUERIES:
        query = query_spec["query"]
        relevant_keywords = query_spec["relevant_keywords"]

        try:
            results = rag.query(query, top_k=top_k)
        except Exception as e:
            logger.warning("Query '%s' failed: %s", query, e)
            continue

        if results.empty:
            per_query.append({
                "query": query,
                "status": "empty",
                "precision_at_3": 0.0,
                "precision_at_5": 0.0,
                "recall_at_5": 0.0,
                "mrr": 0.0,
            })
            continue

        # Auto-label relevance
        labels = _auto_label_relevance(results, relevant_keywords)
        total_relevant_in_results = sum(labels)

        # Also check how many total docs might be relevant (full result set)
        # We use the result set itself as our universe
        p3 = _precision_at_k(labels, 3)
        p5 = _precision_at_k(labels, min(5, len(labels)))
        r5 = _recall_at_k(labels, min(5, len(labels)), total_relevant_in_results)
        mrr = _mrr(labels)

        total_p3 += p3
        total_p5 += p5
        total_r5 += r5
        total_mrr += mrr
        n_queries += 1

        # Check for low-confidence results
        if not JobPulseRAG.has_strong_matches(results):
            low_confidence_count += 1

        per_query.append({
            "query": query,
            "status": "ok",
            "n_results": len(results),
            "top_score": round(float(results["score"].iloc[0]), 3),
            "labels": labels,
            "precision_at_3": round(p3, 3),
            "precision_at_5": round(p5, 3),
            "recall_at_5": round(r5, 3),
            "mrr": round(mrr, 3),
        })

    return {
        "model": "rag_retrieval",
        "status": "ok",
        "n_queries": n_queries,
        "top_k": top_k,
        "avg_precision_at_3": round(total_p3 / n_queries, 3) if n_queries else 0,
        "avg_precision_at_5": round(total_p5 / n_queries, 3) if n_queries else 0,
        "avg_recall_at_5": round(total_r5 / n_queries, 3) if n_queries else 0,
        "avg_mrr": round(total_mrr / n_queries, 3) if n_queries else 0,
        "low_confidence_rate": round(low_confidence_count / n_queries, 3) if n_queries else 0,
        "per_query": per_query,
    }
