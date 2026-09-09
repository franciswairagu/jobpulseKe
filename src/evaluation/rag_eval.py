"""RAG Retrieval & Generation evaluation.

Evaluates:
  1. Retrieval quality: Precision@k, Recall@k, MRR
  2. Generation quality: LLM answer grounding, coherence, helpfulness
"""

import logging
from pathlib import Path
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
      1. Query the RAG system (TF-IDF fallback if sentence-transformers fails)
      2. Auto-label relevance using keyword matching
      3. Compute Precision@k, Recall@k, MRR

    Returns aggregate metrics + per-query detail.
    """
    try:
        rag = JobPulseRAG()
        if rag.store.exists():
            try:
                rag.load()
            except Exception:
                logger.info("Default index load failed, falling back to TF-IDF")
                rag = JobPulseRAG(index_dir=Path(RAG_DATA_DIR) / "tfidf")
                rag.ensure_ready(embedder_prefer="tfidf")
        else:
            logger.info("No default index, building with TF-IDF")
            rag = JobPulseRAG(index_dir=Path(RAG_DATA_DIR) / "tfidf")
            rag.ensure_ready(embedder_prefer="tfidf")
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


# ---------------------------------------------------------------------------
# LLM Generation evaluation
# ---------------------------------------------------------------------------

GENERATION_TEST_QUERIES = [
    {
        "query": "What skills do I need for a mid-level data scientist role?",
        "type": "skill_inquiry",
        "must_contain": ["python", "machine learning", "sql"],
    },
    {
        "query": "Find remote frontend developer jobs",
        "type": "job_search",
        "must_contain": ["frontend", "developer"],
    },
    {
        "query": "How do I become a senior DevOps engineer?",
        "type": "career_advice",
        "must_contain": ["devops", "engineer"],
    },
    {
        "query": "What are the top skills in Kenya?",
        "type": "market_intelligence",
        "must_contain": ["skill", "kenya"],
    },
    {
        "query": "Is Docker a good skill to learn?",
        "type": "skill_inquiry",
        "must_contain": ["docker"],
    },
]


def evaluate_rag_generation(
    use_llm: bool = False,
    top_k: int = 5,
) -> Dict[str, Any]:
    """Evaluate RAG generation quality.

    Tests both LLM-backed and template-based generation.

    Metrics:
      - answer_length: Average answer word count
      - grounding_rate: % of answers that reference retrieved context
      - coherence_score: Simple heuristic (has structure, not empty)
      - method: "llm" or "template"
    """
    from src.rag.assistant import JobPulseAssistant, _detect_question_type
    from src.rag.llm import OllamaLLM

    try:
        rag = JobPulseRAG(index_dir=Path(RAG_DATA_DIR) / "tfidf")
        rag.ensure_ready(embedder_prefer="tfidf")
    except Exception as e:
        logger.error("Failed to load RAG index: %s", e)
        return {"model": "rag_generation", "status": "error", "error": str(e)}

    llm = OllamaLLM() if use_llm else None
    assistant = JobPulseAssistant(rag=rag, llm=llm)

    per_query = []
    total_length = 0
    total_grounding = 0
    total_coherence = 0
    n_queries = 0
    methods_used = {"llm": 0, "template": 0}

    for spec in GENERATION_TEST_QUERIES:
        query = spec["query"]
        expected_type = spec["type"]
        must_contain = spec["must_contain"]

        try:
            result = assistant.ask(query, top_k=top_k)
        except Exception as e:
            logger.warning("Query '%s' failed: %s", query, e)
            continue

        answer = result.answer
        words = answer.split()
        word_count = len(words)

        # Grounding: does the answer reference specific data?
        grounding_keywords = ["posting", "job", "role", "skill", "company", "dataset", "found", "data"]
        grounding = any(kw in answer.lower() for kw in grounding_keywords)

        # Coherence: structural quality heuristic
        has_structure = "**" in answer or "-" in answer or any(c.isdigit() for c in answer)
        coherence = 1.0 if (word_count > 20 and has_structure) else 0.5 if word_count > 10 else 0.0

        # Must-contain check
        contains_expected = all(kw.lower() in answer.lower() for kw in must_contain)

        # Detect actual question type
        detected_type = _detect_question_type(query)
        type_correct = detected_type == expected_type

        method = "llm" if (llm and llm.available and result.method == "llm") else "template"
        methods_used[method] += 1

        total_length += word_count
        total_grounding += int(grounding)
        total_coherence += coherence
        n_queries += 1

        per_query.append({
            "query": query,
            "expected_type": expected_type,
            "detected_type": detected_type,
            "type_correct": type_correct,
            "method": method,
            "answer_length": word_count,
            "grounded": grounding,
            "coherence": round(coherence, 2),
            "contains_expected_keywords": contains_expected,
            "confidence": result.confidence,
        })

    avg_length = total_length / n_queries if n_queries else 0
    grounding_rate = total_grounding / n_queries if n_queries else 0
    avg_coherence = total_coherence / n_queries if n_queries else 0

    return {
        "model": "rag_generation",
        "status": "ok",
        "n_queries": n_queries,
        "use_llm": use_llm,
        "llm_available": llm.available if llm else False,
        "methods_used": methods_used,
        "avg_answer_length": round(avg_length, 1),
        "grounding_rate": round(grounding_rate, 3),
        "avg_coherence": round(avg_coherence, 3),
        "per_query": per_query,
    }
