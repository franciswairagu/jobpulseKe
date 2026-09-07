"""
CV Analyzer adapter.

What is REAL model output vs. reconstructed/deterministic here:

  - skills_found / years_experience / education / certifications /
    seniority_level: real output of `SkillExtractor` (rule-based,
    reconstructed from the notebook's documented interface - see
    app/ml/preprocessing/skill_extractor.py's provenance note).

  - tech_category / tech_category_confidence: the ACTUAL trained
    TF-IDF+LogisticRegression classifier from nlp_analysis.ipynb,
    loaded from CV_CATEGORY_MODEL_PATH if that .joblib artifact
    exists. If it doesn't exist (which is the case in this project
    right now - the artifact was never uploaded), these fields are
    returned as None with classifier_available=False. This adapter
    NEVER fabricates a category or confidence value.

  - cv_score: NOT a model output. The notebook's CV analysis never
    produces a 0-100 score, strengths, or weaknesses - only
    structured extraction + a predicted category. Those three fields
    are a documented, deterministic composite computed in
    app/services/cv_service.py from the real extracted signals above.
    They are labeled score_type="deterministic_composite" everywhere
    they appear so no caller can mistake them for ML output.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.core.config import get_settings
from app.ml.preprocessing.skill_extractor import get_extractor

settings = get_settings()


@dataclass
class CVExtraction:
    skills_found: list[str]
    years_experience: int
    education: list[str]
    certifications: list[str]
    seniority_level: str | None
    tech_category: str | None
    tech_category_confidence: float | None
    classifier_available: bool
    classifier_model_version: str | None


class _ClassifierHandle:
    """Loads the trained tech_category classifier if present. Loaded once,
    reused across requests, per the spec's model-registry requirement."""

    def __init__(self, model_path: str):
        self.model_path = Path(model_path)
        self.pipeline = None
        self.classes_ = None
        self.version = None
        self._load()

    def _load(self) -> None:
        if not self.model_path.is_file():
            return
        try:
            import joblib

            artifact = joblib.load(self.model_path)
            # Support either a bare sklearn pipeline or a dict with metadata,
            # matching how TechCategoryClassifier.save() is described to work.
            if isinstance(artifact, dict):
                self.pipeline = artifact.get("pipeline")
                self.classes_ = artifact.get("classes")
                self.version = artifact.get("trained_at") or artifact.get("version")
            else:
                self.pipeline = artifact
                self.classes_ = getattr(artifact, "classes_", None)
                self.version = "unknown"
        except Exception:
            # Corrupt/incompatible artifact: degrade to unavailable rather
            # than crash CV analysis for every user.
            self.pipeline = None

    @property
    def is_ready(self) -> bool:
        return self.pipeline is not None

    def predict(self, text: str) -> tuple[str | None, float | None]:
        if not self.is_ready:
            return None, None
        try:
            prediction = self.pipeline.predict([text])[0]
            confidence = None
            if hasattr(self.pipeline, "predict_proba"):
                proba = self.pipeline.predict_proba([text])[0]
                confidence = float(max(proba))
            return str(prediction), confidence
        except Exception:
            return None, None


@lru_cache(maxsize=1)
def _get_classifier() -> _ClassifierHandle:
    return _ClassifierHandle(settings.CV_CATEGORY_MODEL_PATH)


class CVAnalyzer:
    """Clean interface required by the integration spec: `analyze(cv_text)`."""

    def __init__(self):
        self.extractor = get_extractor()
        self.classifier = _get_classifier()

    def analyze(self, cv_text: str) -> CVExtraction:
        extracted = self.extractor.extract_skills(cv_text)
        all_skills = sorted({skill for group in extracted.values() for skill in group})
        years_experience = self.extractor.extract_years_experience(cv_text)
        education = self.extractor.extract_education(cv_text)
        certifications = self.extractor.extract_certifications(cv_text)
        seniority_level, _ = self.extractor.extract_seniority(cv_text)

        category, confidence = self.classifier.predict(cv_text)

        return CVExtraction(
            skills_found=all_skills,
            years_experience=years_experience,
            education=education,
            certifications=certifications,
            seniority_level=seniority_level,
            tech_category=category,
            tech_category_confidence=confidence,
            classifier_available=self.classifier.is_ready,
            classifier_model_version=self.classifier.version,
        )

    def health(self) -> dict[str, Any]:
        return {
            "extractor_ready": True,
            "classifier_ready": self.classifier.is_ready,
            "classifier_model_path": str(self.classifier.model_path),
        }
