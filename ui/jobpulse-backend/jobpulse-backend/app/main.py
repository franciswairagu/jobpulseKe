import logging
import os
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import auth, career_insights, cv, dashboard, jobs, rag, recommendations, system
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
        force = os.getenv("FORCE_REINGEST", "").lower() in ("1", "true", "yes")
        if count > 0 and not force:
            logger.info("DB already has %d jobs — skipping auto-ingest", count)
            return
        if force and count > 0:
            logger.info("FORCE_REINGEST=true — clearing %d existing jobs", count)
            db.query(Job).delete()
            db.commit()

        # Check for Docker environment first, then fallback to relative path
        docker_data = Path("/app/data")
        if docker_data.exists():
            data_root = docker_data
        else:
            data_root = Path(__file__).resolve().parent.parent.parent.parent.parent / "data"
        processed_dir = data_root / "processed"

        # Build a list of all candidate files with their row counts,
        # then pick the one with the most rows.
        import pandas as pd
        candidates = []

        # 1. All cleaned parquets (sorted by row count descending)
        if processed_dir.exists():
            for p in processed_dir.glob("jobpulse_cleaned_*.parquet"):
                try:
                    df_tmp = pd.read_parquet(p)
                    candidates.append((str(p), len(df_tmp)))
                    del df_tmp
                except Exception:
                    pass

        # 2. master_full.csv (the largest comprehensive dataset)
        master_full = data_root / "processed" / "master_full.csv"
        if master_full.exists():
            try:
                df_tmp = pd.read_csv(master_full)
                candidates.append((str(master_full), len(df_tmp)))
                del df_tmp
            except Exception:
                pass

        # 3. Configured path
        if Path(settings.JOB_DATASET_PATH).exists():
            try:
                df_tmp = pd.read_parquet(settings.JOB_DATASET_PATH) if settings.JOB_DATASET_PATH.endswith(".parquet") else pd.read_csv(settings.JOB_DATASET_PATH)
                candidates.append((settings.JOB_DATASET_PATH, len(df_tmp)))
                del df_tmp
            except Exception:
                pass

        # 4. External master CSV
        ext_csv = data_root / "external" / "jobpulseke_master_africa_tech_jobs.csv"
        if ext_csv.exists():
            try:
                df_tmp = pd.read_csv(ext_csv)
                candidates.append((str(ext_csv), len(df_tmp)))
                del df_tmp
            except Exception:
                pass

        # 5. Legacy fallback
        legacy = data_root / "processed" / "cleaned_jobs.csv"
        if legacy.exists():
            try:
                df_tmp = pd.read_csv(legacy)
                candidates.append((str(legacy), len(df_tmp)))
                del df_tmp
            except Exception:
                pass

        if not candidates:
            logger.warning("No job data file found for auto-ingest — dashboard will be empty")
            return

        # Pick the candidate with the most rows
        candidates.sort(key=lambda x: x[1], reverse=True)
        data_path, row_count = candidates[0]
        logger.info("Auto-ingest: selected %s (%d rows) from %d candidates: %s",
                     data_path, row_count, len(candidates),
                     [(Path(c[0]).name, c[1]) for c in candidates])

        logger.info("Auto-ingesting jobs from %s", data_path)
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
    # Set startup_id FIRST so the /api/startup-id endpoint is available immediately
    app.state.startup_id = str(uuid.uuid4())
    logger.info("JobPulse backend starting (env=%s, startup_id=%s)", settings.ENVIRONMENT, app.state.startup_id)
    logger.info("CORS origins: %s", settings.CORS_ORIGINS)

    init_db()
    build_registry()
    _auto_ingest_if_empty()

    # Preload RAG assistant and warm up Ollama model (non-blocking)
    try:
        from app.api.rag import _get_assistant
        assistant = _get_assistant()
        if assistant:
            logger.info("RAG assistant preloaded successfully")
            # Warm up Ollama model so first user query is instant
            if assistant.llm and assistant.llm.available:
                logger.info("Warming up Ollama model...")
                assistant.llm.generate(
                    prompt="hi",
                    system="Reply with one word.",
                )
                logger.info("Ollama model warmed up")
        else:
            logger.warning("RAG assistant preload returned None")
    except Exception as e:
        logger.warning("RAG assistant preload failed: %s", e)


@app.on_event("shutdown")
def on_shutdown():
    logger.info("JobPulse backend shutting down")


@app.get("/api/startup-id")
def get_startup_id():
    """Return the unique ID for this server process.

    The frontend stores this on login and compares it on each page load.
    If it changes (server restarted), the frontend forces a logout.
    """
    return {"startup_id": app.state.startup_id}


app.include_router(system.router)
app.include_router(auth.router)
app.include_router(cv.router)
app.include_router(recommendations.router)
app.include_router(jobs.router)
app.include_router(dashboard.router)
app.include_router(rag.router)
app.include_router(career_insights.router)
