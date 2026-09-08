import uuid

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.database import get_db
from app.models.enums import JobStatus
from app.models.job import Job, JobSkill
from app.models.skill import Skill
from app.models.user import User
from app.schemas.job import JobListOut, JobOut, JobStatusHistoryOut, JobStatusUpdate, SkillDemandOut, SkillDemandResponse
from app.services import job_service

router = APIRouter(prefix="/api/jobs", tags=["jobs"])
settings = get_settings()


def _error(code: str, message: str, status_code: int):
    return HTTPException(status_code=status_code, detail={"error": {"code": code, "message": message, "details": {}}})


def _to_job_out(job: Job) -> JobOut:
    required = [link.skill.name for link in job.skill_links if link.skill and not link.is_preferred]
    preferred = [link.skill.name for link in job.skill_links if link.skill and link.is_preferred]
    return JobOut(
        id=job.id, title=job.title, company=job.company, country=job.country, city=job.city,
        remote=job.remote, work_mode=job.work_mode, employment_type=job.employment_type,
        source=job.source, source_url=job.source_url,
        posted_at=job.posted_at, expires_at=job.expires_at, status=job.status.value,
        required_skills=required, preferred_skills=preferred,
    )


@router.get("", response_model=JobListOut)
def list_jobs(
    q: str | None = None,
    country: str | None = None,
    city: str | None = None,
    remote: bool | None = None,
    employment_type: str | None = None,
    status_filter: JobStatus = Query(JobStatus.AVAILABLE, alias="status"),
    skills: list[str] | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=500),
    db: Session = Depends(get_db),
):
    jobs, total = job_service.search_jobs(
        db, query=q, country=country, city=city, remote=remote, employment_type=employment_type,
        status=status_filter, skills=skills, page=page, limit=limit,
    )
    return JobListOut(jobs=[_to_job_out(j) for j in jobs], total=total, page=page, limit=limit)


@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: uuid.UUID, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise _error("JOB_NOT_FOUND", "Job not found.", status.HTTP_404_NOT_FOUND)
    return _to_job_out(job)


@router.get("/{job_id}/history", response_model=list[JobStatusHistoryOut])
def get_job_history(job_id: uuid.UUID, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise _error("JOB_NOT_FOUND", "Job not found.", status.HTTP_404_NOT_FOUND)
    return job.status_history


@router.patch("/{job_id}/status", response_model=JobOut)
def set_job_status(
    job_id: uuid.UUID,
    payload: JobStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        status_enum = JobStatus(payload.status)
    except ValueError:
        raise _error("INVALID_STATUS", f"Status must be one of {[s.value for s in JobStatus]}.", status.HTTP_400_BAD_REQUEST)
    try:
        job = job_service.update_job_status(db, job_id, status_enum, payload.source, payload.confidence, payload.note)
    except ValueError:
        raise _error("JOB_NOT_FOUND", "Job not found.", status.HTTP_404_NOT_FOUND)
    return _to_job_out(job)


@router.post("/ingest")
async def ingest_jobs(
    file: UploadFile | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Ingest jobs from an uploaded CSV/Parquet, or from JOB_DATASET_PATH
    if no file is provided. Expects the pipeline's STANDARD_COLUMNS schema."""
    if file is not None:
        contents = await file.read()
        import io

        if file.filename.lower().endswith(".csv"):
            df = pd.read_csv(io.BytesIO(contents))
        elif file.filename.lower().endswith((".parquet", ".pq")):
            df = pd.read_parquet(io.BytesIO(contents))
        else:
            raise _error("UNSUPPORTED_FILE_TYPE", "Job dataset must be CSV or Parquet.", status.HTTP_400_BAD_REQUEST)
    else:
        try:
            if settings.JOB_DATASET_PATH.endswith(".csv"):
                df = pd.read_csv(settings.JOB_DATASET_PATH)
            else:
                df = pd.read_parquet(settings.JOB_DATASET_PATH)
        except FileNotFoundError:
            raise _error("DATASET_NOT_FOUND", f"No file uploaded and JOB_DATASET_PATH ({settings.JOB_DATASET_PATH}) does not exist.", status.HTTP_404_NOT_FOUND)

    result = job_service.ingest_jobs_from_dataframe(db, df.fillna(""))
    return result


@router.post("/maintenance/mark-stale")
def mark_stale(cutoff_days: int = 30, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    count = job_service.mark_stale_jobs_removed(db, cutoff_days=cutoff_days)
    return {"marked_removed": count}


@router.get("/skills/demand", response_model=SkillDemandResponse)
def skill_demand(
    country: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    # Denominator = jobs that have at least one skill, for meaningful percentages
    skilled_q = (
        db.query(func.count(func.distinct(Job.id)))
        .join(JobSkill, JobSkill.job_id == Job.id)
        .filter(Job.status == JobStatus.AVAILABLE)
    )
    if country and country != "All countries":
        skilled_q = skilled_q.filter(func.lower(Job.country) == country.lower())
    total_skilled = skilled_q.scalar() or 1

    q = (
        db.query(
            Skill.name.label("skill_name"),
            func.count(JobSkill.id).label("demand"),
            func.count(func.distinct(Job.id)).label("job_count"),
        )
        .join(JobSkill, JobSkill.skill_id == Skill.id)
        .join(Job, Job.id == JobSkill.job_id)
        .filter(Job.status == JobStatus.AVAILABLE)
    )
    if country and country != "All countries":
        q = q.filter(func.lower(Job.country) == country.lower())

    rows = (
        q.group_by(Skill.name)
        .order_by(func.count(JobSkill.id).desc())
        .limit(limit)
        .all()
    )

    skills = []
    for row in rows:
        demand_pct = round((row.job_count / total_skilled) * 100)
        # Growth: positive if above median demand, negative if below
        status_label = "Growing" if demand_pct >= 10 else "Stable"
        skills.append(SkillDemandOut(
            skill=row.skill_name,
            demand=demand_pct,
            jobs=row.job_count,
            role=row.skill_name,
            growth=0,
            status=status_label,
        ))

    return SkillDemandResponse(
        skills=skills,
        total=len(skills),
        dataSource={"source": "JobPulseKE database", "collectedAt": __import__("datetime").date.today().isoformat()},
    )
