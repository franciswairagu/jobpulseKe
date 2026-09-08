from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone

import pandas as pd
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.ml.preprocessing.skill_extractor import get_extractor
from app.models.enums import JobStatus
from app.models.job import Job, JobSkill, JobStatusHistory
from app.models.skill import Skill


def _get_or_create_skill(db: Session, name: str) -> Skill:
    existing = db.query(Skill).filter(func.lower(Skill.name) == name.lower()).first()
    if existing:
        return existing
    skill = Skill(name=name)
    db.add(skill)
    db.flush()
    return skill


def _parse_date(value) -> date | None:
    if value is None or value == "":
        return None
    try:
        parsed = pd.to_datetime(value, errors="coerce", format="mixed", dayfirst=True)
        if pd.isna(parsed):
            return None
        return parsed.date()
    except Exception:
        return None


def ingest_jobs_from_dataframe(db: Session, df: pd.DataFrame, source_default: str = "pipeline_import") -> dict:
    """
    Maps the JobPulseKE pipeline's STANDARD_COLUMNS schema
    (job_id, source, job_title, job_description, date_posted, ...)
    onto the backend's Job/JobSkill tables.
    """
    extractor = get_extractor()
    created, updated, skipped = 0, 0, 0

    for idx, row in df.iterrows():
        try:
            source = str(row.get("source") or source_default).strip() or source_default
            source_job_id = str(row.get("source_job_id") or row.get("job_id") or "").strip()
            if not source_job_id:
                continue

            job = (
                db.query(Job)
                .filter(Job.source == source, Job.source_job_id == source_job_id)
                .first()
            )
            is_new = job is None
            if is_new:
                job = Job(source=source, source_job_id=source_job_id, status=JobStatus.UNKNOWN)

            description = str(row.get("job_description") or "")

            job.title = str(row.get("job_title") or job.title or "").strip()[:255]
            job.company = str(row.get("company") or "").strip()[:255] or None
            job.description = description[:65535] or None
            job.country = str(row.get("country") or "").strip()[:100] or None
            job.city = str(row.get("location") or "").strip()[:100] or None
            
            # Determine remote status from work_mode or remote_scope
            work_mode = str(row.get("work_mode") or "").strip().lower()
            remote_scope = str(row.get("remote_scope") or "").strip().lower()
            job.remote = (
                work_mode in ("remote", "hybrid") or 
                remote_scope in ("global", "africa-wide") or
                bool(row.get("remote_eligible"))
            )
            
            job.work_mode = work_mode[:50] or None
            job.employment_type = str(row.get("employment_type") or "").strip()[:50] or None
            job.source_url = str(row.get("vacancy_url") or "").strip()[:1000] or None
            job.posted_at = _parse_date(row.get("date_posted"))
            job.expires_at = _parse_date(row.get("application_deadline"))

            if job.status == JobStatus.UNKNOWN:
                job.status = JobStatus.AVAILABLE

            db.add(job)
            db.flush()

            db.query(JobStatusHistory).filter(
                JobStatusHistory.job_id == job.id,
                JobStatusHistory.source == "ingestion",
                JobStatusHistory.status == job.status,
            )
            db.add(JobStatusHistory(job_id=job.id, status=job.status, source="ingestion", confidence=1.0))

            extracted = extractor.extract_skills(description)
            found_skills = {s for group in extracted.values() for s in group}
            # Also extract from title (many descriptions are empty)
            title = str(row.get("job_title") or job.title or "")
            title_skills = extractor.extract_skills(title)
            found_skills |= {s for group in title_skills.values() for s in group}
            # Extract role-based skills from title (e.g. "Data Scientist" -> machine learning, data science)
            title_role_skills = extractor.extract_title_skills(title)
            found_skills |= {s for group in title_role_skills.values() for s in group}
            existing_links = {link.skill.name for link in job.skill_links if link.skill}
            for skill_name in found_skills - existing_links:
                skill = _get_or_create_skill(db, skill_name)
                db.add(JobSkill(job_id=job.id, skill_id=skill.id, is_preferred=False))

        except Exception:
            db.rollback()
            skipped += 1
            continue

        if is_new:
            created += 1
        else:
            updated += 1

    db.commit()
    return {"created": created, "updated": updated, "skipped": skipped, "total_processed": created + updated}


def mark_stale_jobs_removed(db: Session, cutoff_days: int = 30) -> int:
    """Jobs not re-seen by an ingestion run in `cutoff_days` are marked
    REMOVED. This is CRUD bookkeeping, not a prediction."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=cutoff_days)
    stale_jobs = (
        db.query(Job)
        .filter(Job.status == JobStatus.AVAILABLE, Job.updated_at < cutoff)
        .all()
    )
    for job in stale_jobs:
        job.status = JobStatus.REMOVED
        db.add(job)
        db.add(JobStatusHistory(job_id=job.id, status=JobStatus.REMOVED, source="stale_cutoff", confidence=None,
                                 note=f"Not re-seen by ingestion for {cutoff_days}+ days"))
    db.commit()
    return len(stale_jobs)


def update_job_status(db: Session, job_id: uuid.UUID, status: JobStatus, source: str | None, confidence: float | None, note: str | None) -> Job:
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise ValueError("Job not found")
    job.status = status
    db.add(job)
    db.add(JobStatusHistory(job_id=job.id, status=status, source=source, confidence=confidence, note=note))
    db.commit()
    db.refresh(job)
    return job


def search_jobs(
    db: Session,
    query: str | None = None,
    country: str | None = None,
    city: str | None = None,
    remote: bool | None = None,
    employment_type: str | None = None,
    status: JobStatus = JobStatus.AVAILABLE,
    skills: list[str] | None = None,
    page: int = 1,
    limit: int = 20,
) -> tuple[list[Job], int]:
    q = db.query(Job).options(joinedload(Job.skill_links).joinedload(JobSkill.skill)).filter(Job.status == status)

    if query:
        like = f"%{query.lower()}%"
        q = q.filter(func.lower(Job.title).like(like) | func.lower(func.coalesce(Job.company, "")).like(like))
    if country:
        q = q.filter(func.lower(Job.country) == country.lower())
    if city:
        q = q.filter(func.lower(Job.city) == city.lower())
    if remote is not None:
        q = q.filter(Job.remote == remote)
    if employment_type:
        q = q.filter(func.lower(Job.employment_type) == employment_type.lower())
    if skills:
        q = q.join(JobSkill).join(Skill).filter(func.lower(Skill.name).in_([s.lower() for s in skills])).distinct()

    total = q.count()
    jobs = q.order_by(Job.posted_at.desc().nullslast()).offset((page - 1) * limit).limit(limit).all()
    return jobs, total


def market_insights(db: Session) -> dict:
    """Real DB aggregates only - no forecasting, per product decision."""
    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)

    jobs_added = db.query(Job).filter(Job.created_at >= week_ago).count()
    jobs_removed = (
        db.query(JobStatusHistory)
        .filter(JobStatusHistory.status == JobStatus.REMOVED, JobStatusHistory.timestamp >= week_ago)
        .count()
    )
    total_available = db.query(Job).filter(Job.status == JobStatus.AVAILABLE).count()
    remote_count = db.query(Job).filter(Job.status == JobStatus.AVAILABLE, Job.remote.is_(True)).count()
    remote_pct = round((remote_count / total_available) * 100) if total_available else 0

    top_countries = (
        db.query(Job.country, func.count(Job.id).label("cnt"))
        .filter(Job.status == JobStatus.AVAILABLE, Job.country.isnot(None))
        .group_by(Job.country)
        .order_by(func.count(Job.id).desc())
        .limit(10)
        .all()
    )
    top_skills = (
        db.query(Skill.name, func.count(JobSkill.id).label("cnt"))
        .join(JobSkill, JobSkill.skill_id == Skill.id)
        .join(Job, Job.id == JobSkill.job_id)
        .filter(Job.status == JobStatus.AVAILABLE)
        .group_by(Skill.name)
        .order_by(func.count(JobSkill.id).desc())
        .limit(10)
        .all()
    )

    return {
        "jobs_added_this_week": jobs_added,
        "jobs_removed_this_week": jobs_removed,
        "total_available_jobs": total_available,
        "remote_count": remote_count,
        "remote_pct": remote_pct,
        "top_countries": [{"country": c, "count": n} for c, n in top_countries],
        "top_skills": [{"skill": s, "count": n} for s, n in top_skills],
    }
