"""
RAG Assistant endpoint — answers job-market questions using the
JobPulse retrieval system. No LLM required; the assistant composes
grounded answers from retrieved records alone.
"""
from __future__ import annotations

import logging
import re
import sys
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
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
def ask_rag(
    payload: RAGQueryRequest,
    db: Session = Depends(get_db),
):
    """Ask a job-market question grounded in the indexed JobPulse dataset."""
    try:
        assistant = _get_assistant()

        # For market intelligence questions, fetch actual skill or role demand data
        market_data = None
        if _is_market_intelligence_question(payload.question):
            country = _extract_country_filter(payload.question)
            is_role = _is_role_question(payload.question)

            if is_role:
                market_data = _get_role_demand_data(db, country)
                logger.info("Market intelligence query (roles): country=%s, roles_found=%d",
                           country, len(market_data.get("roles", [])))
            else:
                market_data = _get_skill_demand_data(db, country)
                logger.info("Market intelligence query (skills): country=%s, skills_found=%d",
                           country, len(market_data.get("skills", [])))

        result = assistant.ask(payload.question, top_k=payload.top_k, market_data=market_data)
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
