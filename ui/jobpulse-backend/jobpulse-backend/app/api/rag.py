"""
RAG Assistant endpoint — answers job-market questions using the
JobPulse retrieval system. Uses a local LLM (Ollama) for generation
when available; falls back to template-based answers otherwise.
"""
from __future__ import annotations

import logging
import re
import sys
import time
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models.job import Job, JobSkill
from app.models.skill import Skill
from app.models.enums import JobStatus
from app.models.user import User

logger = logging.getLogger("jobpulse.rag")

router = APIRouter(prefix="/api/rag", tags=["rag"])


# ---------------------------------------------------------------------------
# Market data helpers
# ---------------------------------------------------------------------------

_MARKET_INTELLIGENCE_PATTERNS = [
    r"\b(?:most|top|best|highest|popular)\s+(?:in\s+demand|demanded|common|frequent|popular|wanted|sought|needed|requested)",
    r"\b(?:in\s+demand|trending|growing|fastest\s+growing|emerging)",
    r"\b(?:what|which)\s+(?:skill|technology|role|job|position)\s+(?:is|are)\s+(?:the\s+)?(?:most|top|best|popular|common|needed|demanded)",
    r"\b(?:skill|skills|role|roles|job|jobs)\s+(?:in|across|for)\s+(?:kenya|nigeria|ghana|south\s+africa|egypt|africa)",
    r"\b(?:african|africa|kenya|nigeria|ghana|south\s+africa|egypt)\s+(?:market|tech\s+market|job\s+market)",
    r"\b(?:most|top|best)\s+(?:popular|common|frequent|needed)\s+(?:skill|technology|tool|role|job|position)",
    r"\b(?:skill|technology|tool|role|job)\s+(?:demand|gap|shortage|surplus)",
    r"\b(?:how\s+many|number\s+of)\s+(?:job|role|posting)",
    r"\b(?:market\s+(?:share|data|intelligence|trend|insight))",
    r"\b(?:which\s+skill|what\s+skill|which\s+role|what\s+role|what\s+job|which\s+job).*(?:kenya|nigeria|ghana|south\s+africa|egypt|africa)",
    r"\b(?:needed|available)\s+(?:role|job|position)",
    r"\b(?:most|top)\s+(?:hiring|recruited)",
]

_COUNTRY_PATTERNS = {
    "kenya": r"\b(?:kenya|ke)\b",
    "nigeria": r"\b(?:nigeria|ng)\b",
    "ghana": r"\b(?:ghana|gh)\b",
    "south africa": r"\b(?:south\s+africa|za)\b",
    "egypt": r"\b(?:egypt|eg)\b",
    "rwanda": r"\b(?:rwanda|rw)\b",
    "uganda": r"\b(?:uganda|ug)\b",
    "tanzania": r"\b(?:tanzania|tz)\b",
}


def _is_market_intelligence_question(question: str) -> bool:
    lowered = question.lower()
    return any(re.search(p, lowered) for p in _MARKET_INTELLIGENCE_PATTERNS)


def _is_role_question(question: str) -> bool:
    """Check if the question is about roles/jobs rather than skills."""
    role_keywords = r"\b(?:role|roles|job|jobs|position|positions|hiring)\b"
    return bool(re.search(role_keywords, question.lower()))


def _extract_country_filter(question: str) -> str | None:
    lowered = question.lower()
    for country, pattern in _COUNTRY_PATTERNS.items():
        if re.search(pattern, lowered):
            return country.title()
    return None


def _get_skill_demand_data(db: Session, country: str | None = None) -> dict:
    """Fetch skill demand data from the database."""
    from sqlalchemy import func

    q = (
        db.query(Skill.name, func.count(JobSkill.id).label("cnt"))
        .join(JobSkill, JobSkill.skill_id == Skill.id)
        .join(Job, Job.id == JobSkill.job_id)
        .filter(Job.status == JobStatus.AVAILABLE)
    )

    if country:
        q = q.filter(func.lower(Job.country) == country.lower())

    total_jobs = db.query(Job).filter(Job.status == JobStatus.AVAILABLE)
    if country:
        total_jobs = total_jobs.filter(func.lower(Job.country) == country.lower())
    total_count = total_jobs.count()

    skill_counts = q.group_by(Skill.name).order_by(func.count(JobSkill.id).desc()).limit(20).all()

    skills = []
    for name, count in skill_counts:
        pct = (count / total_count * 100) if total_count > 0 else 0
        skills.append({"name": name, "count": count, "percentage": round(pct, 1)})

    return {
        "skills": skills,
        "total_jobs": total_count,
        "country": country or "Africa",
    }


def _get_role_demand_data(db: Session, country: str | None = None) -> dict:
    """Fetch role/job title demand data from the database."""
    from sqlalchemy import func

    q = (
        db.query(Job.title, func.count(Job.id).label("cnt"))
        .filter(Job.status == JobStatus.AVAILABLE)
    )

    if country:
        q = q.filter(func.lower(Job.country) == country.lower())

    total_jobs = db.query(Job).filter(Job.status == JobStatus.AVAILABLE)
    if country:
        total_jobs = total_jobs.filter(func.lower(Job.country) == country.lower())
    total_count = total_jobs.count()

    role_counts = q.group_by(Job.title).order_by(func.count(Job.id).desc()).limit(20).all()

    roles = []
    for title, count in role_counts:
        pct = (count / total_count * 100) if total_count > 0 else 0
        roles.append({"title": title, "count": count, "percentage": round(pct, 1)})

    return {
        "roles": roles,
        "total_jobs": total_count,
        "country": country or "Africa",
        "is_role_question": True,
    }


def _format_market_answer(question: str, market_data: dict) -> str:
    """Format a readable answer from database market data when RAG index is unavailable."""
    if market_data.get("is_role_question"):
        roles = market_data.get("roles", [])
        country = market_data.get("country", "Africa")
        total = market_data.get("total_jobs", 0)
        if not roles:
            return f"No role data found for {country}."
        lines = [f"Here are the top roles in {country} (out of {total:,} jobs):\n"]
        for r in roles[:10]:
            lines.append(f"- **{r['title']}**: {r['count']} jobs ({r['percentage']}%)")
        return "\n".join(lines)
    else:
        skills = market_data.get("skills", [])
        country = market_data.get("country", "Africa")
        total = market_data.get("total_jobs", 0)
        if not skills:
            return f"No skill data found for {country}."
        lines = [f"Here are the top skills in {country} (out of {total:,} jobs):\n"]
        for s in skills[:10]:
            lines.append(f"- **{s['skill']}**: {s['count']} jobs ({s['percentage']}%)")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Lazy-loaded RAG assistant singleton
# ---------------------------------------------------------------------------
_assistant = None
_rag_available = None  # None = untested, True/False after first attempt
_rag_lock = __import__("threading").Lock()


def _get_assistant():
    global _assistant, _rag_available
    if _assistant is not None:
        return _assistant

    with _rag_lock:
        # Double-check after acquiring lock
        if _assistant is not None:
            return _assistant

        # Find the project root containing src/ — works locally and in Docker.
        project_root = str(Path(__file__).resolve().parent.parent.parent.parent.parent.parent)

        # Docker: src/ is mounted at /app/src, so project root is /app
        docker_app = "/app"
        if Path(docker_app, "src", "rag").exists():
            project_root = docker_app

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
            _rag_available = True
            logger.info("RAG assistant loaded successfully")
            return _assistant
        except Exception as e:
            logger.warning("RAG assistant unavailable: %s", e)
            _rag_available = False
            return None


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class RAGQueryRequest(BaseModel):
    question: str = Field(..., min_length=2, max_length=500, description="Free-text job market question")
    top_k: int = Field(3, ge=1, le=20, description="Number of results to retrieve")


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
    method: str = "template"  # "llm" or "template"


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------
@router.post("/ask", response_model=RAGQueryResponse)
def ask_rag(
    payload: RAGQueryRequest,
    db: Session = Depends(get_db),
):
    """Ask a job-market question grounded in the indexed JobPulse dataset."""
    assistant = _get_assistant()

    # Always try to get market data from DB (works without RAG index)
    market_data = None
    if _is_market_intelligence_question(payload.question):
        country = _extract_country_filter(payload.question)
        is_role = _is_role_question(payload.question)
        if is_role:
            market_data = _get_role_demand_data(db, country)
        else:
            market_data = _get_skill_demand_data(db, country)

    if assistant is None:
        # Fallback: answer from DB market data only
        if market_data:
            answer = _format_market_answer(payload.question, market_data)
            return RAGQueryResponse(answer=answer, confidence="database", sources=[], method="database")
        raise HTTPException(
            status_code=503,
            detail={
                "error": {
                    "code": "RAG_UNAVAILABLE",
                    "message": "RAG assistant is still loading. Please try again in a moment.",
                    "details": {},
                }
            },
        )

    try:
        start_time = time.time()

        result = assistant.ask(payload.question, top_k=payload.top_k, market_data=market_data)
        
        elapsed_time = time.time() - start_time
        logger.info("RAG query completed in %.2f seconds, method=%s", elapsed_time, 
                   "llm" if assistant.llm and assistant.llm.available else "template")

        method = "template"
        if assistant.llm and assistant.llm.available and result.confidence == "grounded":
            method = "llm"

        return RAGQueryResponse(
            answer=result.answer,
            confidence=result.confidence,
            sources=[RAGSource(**s) for s in result.sources],
            method=method,
        )
    except Exception as e:
        logger.exception("RAG query failed")
        if market_data:
            answer = _format_market_answer(payload.question, market_data)
            return RAGQueryResponse(answer=answer, confidence="database", sources=[], method="database")
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "RAG_ERROR", "message": str(e)[:500], "details": {}}},
        )


# ---------------------------------------------------------------------------
# Streaming endpoint (SSE)
# ---------------------------------------------------------------------------
def _sse_generator(question: str, top_k: int, market_data: dict | None, assistant):
    """Server-Sent Events generator for token-by-token streaming."""
    import json
    try:
        for event in assistant.ask_stream(question, top_k=top_k, market_data=market_data):
            if isinstance(event, str):
                # Token chunk
                yield f"data: {json.dumps({'type': 'token', 'content': event})}\n\n"
            else:
                # Final metadata dict
                sources = event.get("sources", [])
                method = event.get("method", "template")
                confidence = event.get("confidence", "grounded")
                yield f"data: {json.dumps({'type': 'done', 'confidence': confidence, 'sources': sources, 'method': method})}\n\n"
    except Exception as exc:
        yield f"data: {json.dumps({'type': 'error', 'message': str(exc)[:500]})}\n\n"
    finally:
        yield "data: [DONE]\n\n"


@router.post("/ask-stream")
async def ask_rag_stream(
    payload: RAGQueryRequest,
    db: Session = Depends(get_db),
):
    """Stream a job-market answer token-by-token via Server-Sent Events."""
    assistant = _get_assistant()

    market_data = None
    if _is_market_intelligence_question(payload.question):
        country = _extract_country_filter(payload.question)
        is_role = _is_role_question(payload.question)
        if is_role:
            market_data = _get_role_demand_data(db, country)
        else:
            market_data = _get_skill_demand_data(db, country)

    if assistant is None:
        # Fallback: stream the DB answer directly
        if market_data:
            answer = _format_market_answer(payload.question, market_data)
            async def _db_stream():
                import json
                yield f"data: {json.dumps({'type': 'token', 'content': answer})}\n\n"
                yield f"data: {json.dumps({'type': 'done', 'confidence': 'database', 'sources': [], 'method': 'database'})}\n\n"
                yield "data: [DONE]\n\n"
            return StreamingResponse(_db_stream(), media_type="text/event-stream",
                                     headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"})
        raise HTTPException(
            status_code=503,
            detail={"error": {"code": "RAG_UNAVAILABLE", "message": "RAG assistant is still loading.", "details": {}}},
        )

    return StreamingResponse(
        _sse_generator(payload.question, payload.top_k, market_data, assistant),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )


@router.post("/clear-history")
def clear_history():
    """Clear conversation history for fresh context."""
    assistant = _get_assistant()
    if assistant:
        assistant.clear_history()
        return {"status": "ok", "message": "Conversation history cleared"}
    return {"status": "ok", "message": "No assistant loaded"}


@router.get("/health")
def rag_health():
    """Check if the RAG index is built, queryable, and LLM status."""
    try:
        assistant = _get_assistant()
        if assistant is None:
            return {
                "status": "unavailable",
                "assistant_loaded": False,
                "llm": "unavailable",
                "message": "RAG module (src/) not found in this environment",
            }

        ready = False
        if assistant.rag and assistant.rag.store:
            ready = assistant.rag.store.exists()

        llm_status = "unavailable"
        if assistant.llm:
            if assistant.llm.available:
                llm_status = f"connected ({assistant.llm.config.model})"
            else:
                llm_status = "disconnected"

        return {
            "status": "ready" if ready else "needs_build",
            "assistant_loaded": _assistant is not None,
            "llm": llm_status,
        }
    except Exception as e:
        return {"status": "error", "message": str(e)[:300]}
