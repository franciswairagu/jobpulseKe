import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.storage import get_storage_backend
from app.database import get_db
from app.ml.preprocessing.cv_parser import SUPPORTED_EXTENSIONS
from app.models.enums import ResumeStatus
from app.models.resume import Resume
from app.models.user import User
from app.schemas.cv import CVAnalysisOut, ResumeStatusOut, ResumeUploadOut, SkillOut
from app.services.cv_service import process_resume

router = APIRouter(prefix="/api/cv", tags=["cv"])
settings = get_settings()


def _error(code: str, message: str, status_code: int, details: dict | None = None):
    return HTTPException(status_code=status_code, detail={"error": {"code": code, "message": message, "details": details or {}}})


def _get_owned_resume(db: Session, cv_id: uuid.UUID, user: User) -> Resume:
    resume = db.query(Resume).filter(Resume.id == cv_id).first()
    if not resume:
        raise _error("RESUME_NOT_FOUND", "CV not found.", status.HTTP_404_NOT_FOUND)
    if resume.user_id != user.id:
        raise _error("FORBIDDEN", "You do not have access to this CV.", status.HTTP_403_FORBIDDEN)
    return resume


@router.post("/upload", response_model=ResumeUploadOut, status_code=status.HTTP_201_CREATED)
async def upload_cv(
    file: UploadFile,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    suffix = "." + file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if suffix not in SUPPORTED_EXTENSIONS:
        raise _error("UNSUPPORTED_FILE_TYPE", "Only PDF and DOCX files are accepted.", status.HTTP_400_BAD_REQUEST)

    contents = await file.read()
    max_bytes = settings.MAX_CV_UPLOAD_MB * 1024 * 1024
    if len(contents) == 0:
        raise _error("EMPTY_FILE", "Uploaded file is empty.", status.HTTP_400_BAD_REQUEST)
    if len(contents) > max_bytes:
        raise _error("FILE_TOO_LARGE", f"File exceeds {settings.MAX_CV_UPLOAD_MB}MB limit.", status.HTTP_400_BAD_REQUEST)

    storage = get_storage_backend()
    storage_key = storage.save(contents, file.filename)

    resume = Resume(
        user_id=current_user.id,
        original_filename=file.filename,
        storage_key=storage_key,
        status=ResumeStatus.UPLOADING,
        stage="UPLOADING",
        progress=10,
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)

    return ResumeUploadOut(resume_id=resume.id, status=resume.status.value, uploaded_at=resume.uploaded_at)


@router.post("/{cv_id}/analyze", response_model=ResumeStatusOut, status_code=status.HTTP_202_ACCEPTED)
def analyze_cv(
    cv_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    resume = _get_owned_resume(db, cv_id, current_user)
    if resume.status == ResumeStatus.COMPLETED:
        raise _error("ALREADY_ANALYZED", "This CV has already been analyzed.", status.HTTP_409_CONFLICT)
    if not resume.storage_key:
        raise _error("FILE_UNAVAILABLE", "Uploaded file is no longer available for analysis.", status.HTTP_410_GONE)

    try:
        from app.workers.tasks import analyze_resume_task

        analyze_resume_task.delay(str(resume.id))
    except Exception:
        # Celery/Redis not reachable in this environment (e.g. local dev
        # without a broker running) - fall back to an in-process background
        # task so the endpoint still returns immediately without blocking.
        from app.database import SessionLocal

        def _run():
            worker_db = SessionLocal()
            try:
                fresh = worker_db.query(Resume).filter(Resume.id == resume.id).first()
                if fresh:
                    process_resume(worker_db, fresh)
            finally:
                worker_db.close()

        background_tasks.add_task(_run)

    resume.status = ResumeStatus.PREPROCESSING
    resume.stage = "PREPROCESSING"
    resume.progress = 15
    db.add(resume)
    db.commit()

    return ResumeStatusOut(status=resume.status.value, stage=resume.stage, progress=resume.progress)


@router.get("/{cv_id}/status", response_model=ResumeStatusOut)
def get_status(cv_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    resume = _get_owned_resume(db, cv_id, current_user)
    return ResumeStatusOut(status=resume.status.value, stage=resume.stage, progress=resume.progress, error_message=resume.error_message)


@router.get("/{cv_id}", response_model=CVAnalysisOut)
def get_analysis(cv_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    resume = _get_owned_resume(db, cv_id, current_user)
    if not resume.analysis:
        raise _error("ANALYSIS_NOT_READY", "CV analysis is not complete yet.", status.HTTP_409_CONFLICT)
    analysis = resume.analysis
    return CVAnalysisOut(
        resume_id=resume.id,
        cv_score=analysis.cv_score,
        score_type=analysis.score_type,
        tech_category=analysis.tech_category,
        tech_category_confidence=analysis.tech_category_confidence,
        classifier_available=analysis.classifier_available,
        skills=[SkillOut(name=s) for s in analysis.skills_found],
        years_experience=analysis.years_experience,
        education=analysis.education,
        certifications=analysis.certifications,
        seniority_level=analysis.seniority_level,
        strengths=analysis.strengths,
        weaknesses=analysis.weaknesses,
        missing_skills=analysis.missing_skills,
        created_at=analysis.created_at,
    )
