import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import auth, cv, dashboard, jobs, rag, recommendations, system
from app.core.config import get_settings
from app.database import SessionLocal, init_db
from app.ml.registry.registry import build_registry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("jobpulse")

settings = get_settings()

app = FastAPI(
    title="JobPulse API",
    description="Career intelligence backend integrating the CV NLP extractor, job recommender, and job-availability tracking.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if isinstance(exc.detail, dict) and "error" in exc.detail:
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": "HTTP_ERROR", "message": str(exc.detail), "details": {}}},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"error": {"code": "VALIDATION_ERROR", "message": "Request validation failed.", "details": {"errors": exc.errors()}}},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": {"code": "INTERNAL_SERVER_ERROR", "message": "An unexpected error occurred.", "details": {}}},
    )


def _auto_ingest_if_empty():
    """Load job data from CSV on first startup if the DB has no jobs."""
    from app.models.job import Job
    from app.models.enums import JobStatus

    db = SessionLocal()
    try:
        count = db.query(Job).filter(Job.status == JobStatus.AVAILABLE).count()
        if count > 0:
            logger.info("DB already has %d jobs — skipping auto-ingest", count)
            return

        # Find a data file to ingest
        candidates = [
            settings.JOB_DATASET_PATH,
            str(Path(__file__).resolve().parent.parent.parent.parent.parent / "data" / "processed" / "cleaned_jobs.csv"),
            str(Path(__file__).resolve().parent.parent.parent.parent.parent / "data" / "external" / "jobpulseke_master_africa_tech_jobs.csv"),
        ]
        data_path = None
        for p in candidates:
            if Path(p).exists():
                data_path = p
                break

        if not data_path:
            logger.warning("No job data file found for auto-ingest — dashboard will be empty")
            return

        logger.info("Auto-ingesting jobs from %s", data_path)
        import pandas as pd
        if data_path.endswith(".csv"):
            df = pd.read_csv(data_path).fillna("")
        else:
            df = pd.read_parquet(data_path).fillna("")

        from app.services.job_service import ingest_jobs_from_dataframe
        result = ingest_jobs_from_dataframe(db, df)
        logger.info("Auto-ingest complete: %s", result)
    except Exception as e:
        logger.error("Auto-ingest failed: %s", e)
        db.rollback()
    finally:
        db.close()


@app.on_event("startup")
def on_startup():
    init_db()
    build_registry()
    _auto_ingest_if_empty()
    logger.info("JobPulse backend started (env=%s)", settings.ENVIRONMENT)


app.include_router(system.router)
app.include_router(auth.router)
app.include_router(cv.router)
app.include_router(recommendations.router)
app.include_router(jobs.router)
app.include_router(dashboard.router)
app.include_router(rag.router)
