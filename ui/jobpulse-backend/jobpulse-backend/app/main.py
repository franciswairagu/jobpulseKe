import logging

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import auth, cv, dashboard, jobs, recommendations, system
from app.core.config import get_settings
from app.database import init_db
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
    # Route handlers raise HTTPException(detail={"error": {...}}) per the
    # spec's consistent error shape. FastAPI's default handler would nest
    # that under an extra "detail" key - unwrap it back to {"error": {...}}.
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


@app.on_event("startup")
def on_startup():
    init_db()
    build_registry()
    logger.info("JobPulse backend started (env=%s)", settings.ENVIRONMENT)


app.include_router(system.router)
app.include_router(auth.router)
app.include_router(cv.router)
app.include_router(recommendations.router)
app.include_router(jobs.router)
app.include_router(dashboard.router)
