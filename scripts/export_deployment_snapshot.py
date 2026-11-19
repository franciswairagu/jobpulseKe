#!/usr/bin/env python3
"""Export the local JobPulse database as the dataset baked into deployments."""
import csv
import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "ui" / "jobpulse-backend" / "jobpulse-backend"
DEFAULT_DATABASE = BACKEND_ROOT / "jobpulse.db"
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "processed" / "deployment_snapshot.csv"

sys.path.insert(0, str(BACKEND_ROOT))
os.environ.setdefault("DATABASE_URL", f"sqlite:///{DEFAULT_DATABASE}")

from sqlalchemy.orm import joinedload

from app.database import SessionLocal
from app.models.enums import JobStatus
from app.models.job import Job, JobSkill


FIELDNAMES = [
    "job_id",
    "source",
    "source_job_id",
    "job_title",
    "company",
    "job_description",
    "location",
    "country",
    "work_mode",
    "remote_scope",
    "job_field",
    "industry",
    "employment_type",
    "experience_required",
    "education_required",
    "salary",
    "currency",
    "date_posted",
    "application_deadline",
    "tech_category",
    "vacancy_url",
    "scraped_at",
    "remote_eligible",
    "extracted_skills",
]


def _value(value):
    return value.isoformat() if value is not None else ""


def export_snapshot(output_path: Path = DEFAULT_OUTPUT) -> int:
    db = SessionLocal()
    try:
        jobs = (
            db.query(Job)
            .options(joinedload(Job.skill_links).joinedload(JobSkill.skill))
            .filter(Job.status == JobStatus.AVAILABLE)
            .order_by(Job.source, Job.source_job_id)
            .all()
        )
        if any(not job.source or not job.source_job_id for job in jobs):
            raise ValueError("Every available job must have a source and source_job_id")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", newline="", encoding="utf-8") as output:
            writer = csv.DictWriter(output, fieldnames=FIELDNAMES, lineterminator="\n")
            writer.writeheader()
            for job in jobs:
                writer.writerow(
                    {
                        "job_id": str(job.id),
                        "source": job.source,
                        "source_job_id": job.source_job_id,
                        "job_title": job.title or "",
                        "company": job.company or "",
                        "job_description": job.description or "",
                        "location": job.city or "",
                        "country": job.country or "",
                        "work_mode": job.work_mode or "",
                        "remote_scope": "",
                        "job_field": "",
                        "industry": "",
                        "employment_type": job.employment_type or "",
                        "experience_required": "",
                        "education_required": "",
                        "salary": "",
                        "currency": "",
                        "date_posted": _value(job.posted_at),
                        "application_deadline": _value(job.expires_at),
                        "tech_category": "",
                        "vacancy_url": job.source_url or "",
                        "scraped_at": _value(job.created_at),
                        "remote_eligible": int(job.remote),
                        "extracted_skills": json.dumps(
                            sorted(
                                link.skill.name
                                for link in job.skill_links
                                if link.skill
                            ),
                            ensure_ascii=True,
                        ),
                    }
                )
        return len(jobs)
    finally:
        db.close()


if __name__ == "__main__":
    count = export_snapshot()
    print(f"Exported {count:,} available jobs to {DEFAULT_OUTPUT}")
