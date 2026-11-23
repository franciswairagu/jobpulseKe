from pathlib import Path
import stat

import app.services.cv_service as cv_service
from app.core.storage import LocalStorageBackend
from app.ml.adapters.cv_analyzer import CVExtraction
from app.models.enums import ResumeStatus
from app.models.resume import Resume
from app.models.user import User


def test_analysis_keeps_original_cv_and_latest_analysis(db_session, monkeypatch, tmp_path):
    user = User(email="cv-owner@example.com", hashed_password="oauth-only")
    db_session.add(user)
    db_session.flush()

    storage = LocalStorageBackend(str(tmp_path / "uploads"))
    storage_key = storage.save(b"stored cv", "resume.pdf")
    resume = Resume(
        user_id=user.id,
        original_filename="resume.pdf",
        storage_key=storage_key,
        status=ResumeStatus.UPLOADING,
        stage="UPLOADING",
        progress=10,
    )
    db_session.add(resume)
    db_session.commit()

    extraction = CVExtraction(
        skills_found=["python", "sql"],
        years_experience=4,
        education=[],
        certifications=[],
        seniority_level="Mid",
        tech_category=None,
        tech_category_confidence=None,
        classifier_available=False,
        classifier_model_version=None,
    )

    class FakeAnalyzer:
        def analyze(self, text):
            return extraction

    monkeypatch.setattr(cv_service, "get_storage_backend", lambda: storage)
    monkeypatch.setattr(cv_service, "CVAnalyzer", FakeAnalyzer)
    monkeypatch.setattr(cv_service.cv_parser, "validate_file", lambda path: None)
    monkeypatch.setattr(cv_service.cv_parser, "extract_text", lambda path: "resume text")

    cv_service.process_resume(db_session, resume)
    db_session.refresh(resume)

    assert resume.status == ResumeStatus.COMPLETED
    assert resume.storage_key == storage_key
    assert Path(storage_key).is_file()
    assert stat.S_IMODE(Path(storage_key).stat().st_mode) == 0o600
    assert resume.analysis is not None
    assert resume.analysis.skills_found == ["python", "sql"]
