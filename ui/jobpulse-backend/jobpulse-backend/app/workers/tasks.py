import pandas as pd

from app.database import SessionLocal
from app.models.resume import Resume
from app.services.cv_service import process_resume
from app.services.job_service import ingest_jobs_from_dataframe, mark_stale_jobs_removed
from app.workers.celery_app import celery_app


@celery_app.task(name="app.workers.tasks.analyze_resume_task", bind=True, max_retries=2)
def analyze_resume_task(self, resume_id: str):
    db = SessionLocal()
    try:
        resume = db.query(Resume).filter(Resume.id == resume_id).first()
        if not resume:
            return {"error": "resume not found"}
        process_resume(db, resume)
        return {"resume_id": resume_id, "status": "COMPLETED"}
    except Exception as exc:
        raise self.retry(exc=exc, countdown=10)
    finally:
        db.close()


@celery_app.task(name="app.workers.tasks.ingest_jobs_task")
def ingest_jobs_task(dataset_path: str):
    db = SessionLocal()
    try:
        df = pd.read_parquet(dataset_path) if dataset_path.endswith((".parquet", ".pq")) else pd.read_csv(dataset_path)
        return ingest_jobs_from_dataframe(db, df.fillna(""))
    finally:
        db.close()


@celery_app.task(name="app.workers.tasks.mark_stale_jobs_task")
def mark_stale_jobs_task(cutoff_days: int = 30):
    db = SessionLocal()
    try:
        count = mark_stale_jobs_removed(db, cutoff_days=cutoff_days)
        return {"marked_removed": count}
    finally:
        db.close()
