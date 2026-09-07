"""
RAG Assistant endpoint — answers job-market questions using the
JobPulse retrieval system. No LLM required; the assistant composes
grounded answers from retrieved records alone.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger("jobpulse.rag")

router = APIRouter(prefix="/api/rag", tags=["rag"])

# ---------------------------------------------------------------------------
# Lazy-loaded RAG assistant singleton
# ---------------------------------------------------------------------------
_assistant = None


def _get_assistant():
    global _assistant
    if _assistant is not None:
        return _assistant

    # Ensure the project root (containing src/) is on sys.path so we can
    # import src.rag.* from the backend process.
    project_root = str(Path(__file__).resolve().parent.parent.parent.parent.parent.parent)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    try:
        from src.rag.assistant import JobPulseAssistant
        _assistant = JobPulseAssistant()
        # Try loading the existing index; if it fails (e.g. sentence-
        # transformers not available), rebuild with TF-IDF.
        try:
            _assistant.rag.ensure_ready()
        except Exception as e:
            logger.warning("Existing RAG index load failed (%s), rebuilding with TF-IDF...", e)
            _assistant.rag.store = None
            from src.rag.retriever import JobPulseRAG
            from src.config import RAG_DATA_DIR
            _assistant.rag = JobPulseRAG(index_dir=Path(RAG_DATA_DIR) / "tfidf")
            _assistant.rag.ensure_ready(embedder_prefer="tfidf")
        logger.info("RAG assistant loaded successfully")
        return _assistant
    except Exception as e:
        logger.error("Failed to load RAG assistant: %s", e)
        raise


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class RAGQueryRequest(BaseModel):
    question: str = Field(..., min_length=2, max_length=500, description="Free-text job market question")
    top_k: int = Field(5, ge=1, le=20, description="Number of results to retrieve")


class RAGSource(BaseModel):
    job_id: str
    title: str
    company: str
    url: str
    score: float


class RAGQueryResponse(BaseModel):
    answer: str
    confidence: str
    sources: list[RAGSource]


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------
@router.post("/ask", response_model=RAGQueryResponse)
def ask_rag(payload: RAGQueryRequest):
    """Ask a job-market question grounded in the indexed JobPulse dataset."""
    try:
        assistant = _get_assistant()
        result = assistant.ask(payload.question, top_k=payload.top_k)
        return RAGQueryResponse(
            answer=result.answer,
            confidence=result.confidence,
            sources=[RAGSource(**s) for s in result.sources],
        )
    except Exception as e:
        logger.exception("RAG query failed")
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "RAG_ERROR", "message": str(e)[:500], "details": {}}},
        )


@router.get("/health")
def rag_health():
    """Check if the RAG index is built and queryable."""
    try:
        assistant = _get_assistant()
        if assistant.rag and assistant.rag.store:
            ready = assistant.rag.store.exists()
        else:
            ready = False
        return {"status": "ready" if ready else "needs_build", "assistant_loaded": _assistant is not None}
    except Exception as e:
        return {"status": "error", "message": str(e)[:300]}
