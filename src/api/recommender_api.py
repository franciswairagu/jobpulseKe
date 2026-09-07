"""FastAPI endpoints for CV-upload based job recommendations."""

import tempfile
from dataclasses import asdict
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile

from src.cv import UnsupportedCVFormatError, extract_text, profile_from_text
from src.recommender import JobRecommender, load_jobs

app = FastAPI(title="JobPulse Recommender", version="1.0.0")


@app.post("/recommend")
async def recommend(
    cv: UploadFile = File(..., description="Candidate CV: .txt, .pdf, or .docx"),
    jobs_path: str = "",
    top_k: int = 10,
):
    """Return matches and targeted actions; uploaded CVs are deleted immediately."""
    if not jobs_path:
        raise HTTPException(422, "jobs_path is required and must point to a JobPulse CSV or Parquet export.")
    suffix = Path(cv.filename or "candidate.txt").suffix.lower()
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temporary:
            temporary.write(await cv.read())
            temporary_path = Path(temporary.name)
        try:
            candidate = profile_from_text(extract_text(temporary_path))
            plan = JobRecommender().build_plan(candidate, load_jobs(jobs_path), top_k)
            return asdict(plan)
        finally:
            temporary_path.unlink(missing_ok=True)
    except (FileNotFoundError, ValueError, UnsupportedCVFormatError) as exc:
        raise HTTPException(400, str(exc)) from exc
