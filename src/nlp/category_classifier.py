"""
TechCategoryClassifier
=======================

This module turns the classification section of
`notebooks/nlp_analysis.ipynb` (previously a run of loose, top-to-bottom
cells) into a single reusable class. The notebook now just *calls* this
class; all the modelling logic lives here so it can be:

  1. Hyperparameter-tuned with `GridSearchCV` instead of trained once with
     hardcoded defaults (`tune()`).
  2. Saved/loaded as one artifact so any backend process (FastAPI, a script,
     a worker) can load a trained model without re-running the notebook
     (`save()` / `TechCategoryClassifier.load()`).
  3. Reused to analyze a candidate CV the exact same way it analyzes a job
     posting — skills, seniority signal, predicted tech category — and
     persist that analysis to disk (`analyze_cv()`), which is the
     "save the analyzed CV" requirement. The raw CV text/file is
     deliberately never written to disk here (consistent with
     `src/cv/parser.py`'s "never persist uploaded documents" policy) —
     only the *extracted, analyzed* data is saved.

Typical usage
-------------
Training (e.g. inside the notebook or a retraining script)::

    from src.nlp.category_classifier import TechCategoryClassifier

    clf = TechCategoryClassifier()
    df = clf.load_training_data()
    X_train, X_test, y_train, y_test = clf.prepare_dataset(df)
    clf.tune(X_train, y_train)          # GridSearchCV hyperparameter tuning
    clf.evaluate(X_test, y_test)
    clf.save()                          # -> src/models/tech_category_classifier.joblib

Serving (e.g. inside a FastAPI endpoint)::

    clf = TechCategoryClassifier.load()
    result = clf.analyze_cv(cv_text, source_filename="jane_doe_cv.pdf")
    # result is already saved to data/nlp/analyzed_cvs/<timestamp>_<id>.json
"""
from __future__ import annotations

import json
import logging
import sys
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import GridSearchCV, StratifiedKFold, train_test_split
from sklearn.pipeline import Pipeline

from src.config import ANALYZED_CV_DIR, MODELS_DIR, PROCESSED_DATA_DIR
from src.nlp.metadata_extractor import get_metadata_extractor
from src.nlp.skill_extractor import get_extractor

logger = logging.getLogger(__name__)

DEFAULT_MODEL_PATH = MODELS_DIR / "tech_category_classifier.joblib"

PLACEHOLDER_STRINGS = {
    "no description", "n/a", "none", "not available", "description not available", "",
}
MIN_REAL_DESCRIPTION_LENGTH = 40

# Same normalization the notebook applied to `tech_category` labels before
# modelling — kept here so training and serving can never drift apart.
CATEGORY_NORMALIZATION = {
    "Cloud & DevOps": "DevOps & Cloud",
    "Product & UX": "Product & Design",
}

# Default hyperparameter search space for tune(). Kept modest so a grid
# search finishes in a reasonable time on a laptop; pass a custom
# `param_grid` to tune() for a wider/narrower search.
DEFAULT_PARAM_GRID = {
    "tfidf__max_features": [1500, 3000, 5000],
    "tfidf__ngram_range": [(1, 1), (1, 2)],
    "tfidf__min_df": [1, 2],
    "clf__C": [0.1, 1.0, 5.0, 10.0],
}


@dataclass
class CVAnalysis:
    """Structured result of analyzing one CV. This — not the raw CV — is
    what gets persisted to disk and what a backend should hand back to a
    caller."""

    cv_id: str
    analyzed_at: str
    source_filename: Optional[str]
    candidate_name: str
    skills: List[str]
    years_experience: int
    education: List[str]
    certifications: List[str]
    seniority_level: Optional[str]
    predicted_tech_category: Optional[str]
    prediction_confidence: Optional[float]
    top_category_probabilities: Dict[str, float] = field(default_factory=dict)
    saved_path: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cv_id": self.cv_id,
            "analyzed_at": self.analyzed_at,
            "source_filename": self.source_filename,
            "candidate_name": self.candidate_name,
            "skills": self.skills,
            "years_experience": self.years_experience,
            "education": self.education,
            "certifications": self.certifications,
            "seniority_level": self.seniority_level,
            "predicted_tech_category": self.predicted_tech_category,
            "prediction_confidence": self.prediction_confidence,
            "top_category_probabilities": self.top_category_probabilities,
            "saved_path": self.saved_path,
        }


class TechCategoryClassifier:
    """TF-IDF + Logistic Regression classifier that predicts `tech_category`
    from job-posting (or CV) text, with hyperparameter tuning, persistence,
    and CV analysis built in.
    """

    def __init__(self, model_path: Optional[Path] = None):
        self.model_path = Path(model_path) if model_path else DEFAULT_MODEL_PATH
        self.pipeline: Optional[Pipeline] = None
        self.best_params_: Optional[Dict[str, Any]] = None
        self.cv_results_: Optional[pd.DataFrame] = None
        self.classes_: Optional[List[str]] = None
        self.trained_at: Optional[str] = None
        self.training_text_column: Optional[str] = None

        self._skill_extractor = get_extractor()
        self._metadata_extractor = get_metadata_extractor()

    # ------------------------------------------------------------------
    # Data loading / cleaning (promoted from notebook cells 2-12)
    # ------------------------------------------------------------------
    @staticmethod
    def is_real_description(text: str) -> bool:
        if not isinstance(text, str):
            return False
        cleaned = text.strip().lower()
        if cleaned in PLACEHOLDER_STRINGS:
            return False
        return len(text.strip()) >= MIN_REAL_DESCRIPTION_LENGTH

    @staticmethod
    def clean_text(raw: str) -> str:
        if not isinstance(raw, str) or not raw.strip():
            return ""
        if "<" in raw and ">" in raw:
            from bs4 import BeautifulSoup
            raw = BeautifulSoup(raw, "html.parser").get_text(separator=" ")
        return " ".join(raw.split())

    def load_training_data(self, path: Optional[Path] = None) -> pd.DataFrame:
        """Load the latest cleaned dataset and prepare it for modelling:
        flags placeholder descriptions, normalizes `tech_category` labels,
        and builds `title_clean` / `desc_clean` / `text_for_nlp`.
        """
        if path is None:
            candidates = sorted(
                PROCESSED_DATA_DIR.glob("jobpulse_cleaned_*.parquet"),
                key=lambda p: p.stat().st_mtime,
            )
            if not candidates:
                raise FileNotFoundError(
                    f"No cleaned dataset found in {PROCESSED_DATA_DIR} "
                    "(looked for jobpulse_cleaned_*.parquet)."
                )
            path = candidates[-1]

        df = pd.read_parquet(path)
        df["has_real_description"] = df["job_description"].apply(self.is_real_description)
        df["tech_category"] = df["tech_category"].replace(CATEGORY_NORMALIZATION)
        df["title_clean"] = df["job_title"].apply(self.clean_text)
        df["desc_clean"] = np.where(
            df["has_real_description"],
            df["job_description"].apply(self.clean_text),
            "",
        )
        df["text_for_nlp"] = (df["title_clean"] + " " + df["desc_clean"]).str.strip()
        logger.info("Loaded %s training rows from %s", len(df), path)
        return df

    def prepare_dataset(
        self,
        df: pd.DataFrame,
        text_column: str = "text_for_nlp",
        min_rows_per_class: int = 8,
        test_size: float = 0.25,
        random_state: int = 42,
    ) -> Tuple[pd.Series, pd.Series, pd.Series, pd.Series]:
        """Filter to real-description rows, drop classes too small to
        evaluate honestly, and produce a stratified train/test split.
        """
        real_df = df[df["has_real_description"]].dropna(subset=["tech_category"]).copy()

        class_counts = real_df["tech_category"].value_counts()
        keep_classes = class_counts[class_counts >= min_rows_per_class].index
            
        dropped = class_counts[class_counts < min_rows_per_class]
        if len(dropped) > 0:
            logger.info("Dropping classes with too few rows to evaluate honestly: %s", dict(dropped))

        model_df = real_df[real_df["tech_category"].isin(keep_classes)]
        self.training_text_column = text_column

        X_train, X_test, y_train, y_test = train_test_split(
            model_df[text_column],
            model_df["tech_category"],
            test_size=test_size,
            random_state=random_state,
            stratify=model_df["tech_category"],
        )
        return X_train, X_test, y_train, y_test

    # ------------------------------------------------------------------
    # Hyperparameter tuning + training
    # ------------------------------------------------------------------
    def tune(
        self,
        X_train: pd.Series,
        y_train: pd.Series,
        param_grid: Optional[Dict[str, List[Any]]] = None,
        cv: int = 5,
        scoring: str = "f1_macro",
        n_jobs: int = -1,
    ) -> Dict[str, Any]:
        """Grid-search a TF-IDF + LogisticRegression pipeline and keep the
        best estimator as `self.pipeline`. Returns the best params + score
        so a caller (or the notebook) can display/log them.
        """
        param_grid = param_grid or DEFAULT_PARAM_GRID

        base_pipeline = Pipeline([
            ("tfidf", TfidfVectorizer(stop_words="english")),
            ("clf", LogisticRegression(max_iter=2000, class_weight="balanced")),
        ])

        # Cap folds at the smallest class size so StratifiedKFold never
        # errors out on a rare category during the search.
        min_class_count = y_train.value_counts().min()
        n_splits = max(2, min(cv, int(min_class_count)))
        splitter = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)

        search = GridSearchCV(
            base_pipeline,
            param_grid=param_grid,
            cv=splitter,
            scoring=scoring,
            n_jobs=n_jobs,
            refit=True,
        )
        search.fit(X_train, y_train)

        self.pipeline = search.best_estimator_
        self.best_params_ = search.best_params_
        self.cv_results_ = pd.DataFrame(search.cv_results_)
        self.classes_ = list(self.pipeline.named_steps["clf"].classes_)
        self.trained_at = datetime.now().isoformat()

        logger.info("Best params: %s (%s=%.4f)", search.best_params_, scoring, search.best_score_)
        return {
            "best_params": search.best_params_,
            "best_score": search.best_score_,
            "scoring": scoring,
            "n_splits": n_splits,
        }

    def train(self, X_train: pd.Series, y_train: pd.Series, params: Optional[Dict[str, Any]] = None) -> None:
        """Fit a single pipeline directly (no search) — useful for a quick
        baseline before calling `tune()`, or to refit on more data using
        params already found by `tune()`.
        """
        pipeline = Pipeline([
            ("tfidf", TfidfVectorizer(stop_words="english")),
            ("clf", LogisticRegression(max_iter=2000, class_weight="balanced")),
        ])
        if params:
            pipeline.set_params(**params)
        pipeline.fit(X_train, y_train)
        self.pipeline = pipeline
        self.classes_ = list(pipeline.named_steps["clf"].classes_)
        self.trained_at = datetime.now().isoformat()

    def evaluate(self, X_test: pd.Series, y_test: pd.Series) -> Dict[str, Any]:
        """Evaluate the currently-fitted pipeline. Call after `tune()` or
        `train()`."""
        self._require_fitted()
        preds = self.pipeline.predict(X_test)
        report = classification_report(y_test, preds, zero_division=0, output_dict=True)
        return {
            "accuracy": accuracy_score(y_test, preds),
            "f1_macro": f1_score(y_test, preds, average="macro", zero_division=0),
            "report": report,
        }

    # ------------------------------------------------------------------
    # Inference
    # ------------------------------------------------------------------
    def predict(self, texts: List[str]) -> List[Dict[str, Any]]:
        """Predict tech_category for a batch of texts, with confidence and
        a small per-class probability breakdown — this is what both a job
        posting classification call and a CV analysis call use under the
        hood."""
        self._require_fitted()
        if isinstance(texts, str):
            texts = [texts]
        probs = self.pipeline.predict_proba(texts)
        classes = self.pipeline.named_steps["clf"].classes_
        results = []
        for row in probs:
            order = np.argsort(row)[::-1]
            top_label = classes[order[0]]
            top_conf = float(row[order[0]])
            top3 = {classes[i]: float(row[i]) for i in order[:3]}
            results.append({
                "predicted_tech_category": top_label,
                "prediction_confidence": top_conf,
                "top_category_probabilities": top3,
            })
        return results

    def _require_fitted(self) -> None:
        if self.pipeline is None:
            raise RuntimeError(
                "No trained pipeline. Call tune()/train() first, or load a "
                "saved model with TechCategoryClassifier.load()."
            )

    # ------------------------------------------------------------------
    # Persistence — this is the "integrate with a backend" piece: any
    # process (a FastAPI app, a script, a notebook) loads the exact same
    # artifact rather than re-training.
    # ------------------------------------------------------------------
    def save(self, path: Optional[Path] = None) -> Path:
        self._require_fitted()
        import joblib

        path = Path(path) if path else self.model_path
        path.parent.mkdir(parents=True, exist_ok=True)
        artifact = {
            "pipeline": self.pipeline,
            "best_params": self.best_params_,
            "classes": self.classes_,
            "trained_at": self.trained_at,
            "training_text_column": self.training_text_column,
        }
        joblib.dump(artifact, path)
        logger.info("Saved trained model to %s", path)
        return path

    @classmethod
    def load(cls, path: Optional[Path] = None) -> "TechCategoryClassifier":
        import joblib

        path = Path(path) if path else DEFAULT_MODEL_PATH
        if not path.exists():
            raise FileNotFoundError(
                f"No saved model at {path}. Train and call .save() first."
            )
        artifact = joblib.load(path)
        instance = cls(model_path=path)
        instance.pipeline = artifact["pipeline"]
        instance.best_params_ = artifact.get("best_params")
        instance.classes_ = artifact.get("classes")
        instance.trained_at = artifact.get("trained_at")
        instance.training_text_column = artifact.get("training_text_column")
        logger.info("Loaded trained model from %s (trained_at=%s)", path, instance.trained_at)
        return instance

    def is_ready(self) -> bool:
        """Cheap health-check a backend can call at startup / in a
        `/health` endpoint."""
        return self.pipeline is not None

    # ------------------------------------------------------------------
    # CV analysis — extract structured data from a CV, predict its most
    # likely tech category, and persist the *analyzed* result to disk.
    # ------------------------------------------------------------------
    def analyze_cv(
        self,
        cv_text: str,
        source_filename: Optional[str] = None,
        candidate_name: str = "",
        save: bool = True,
        output_dir: Optional[Path] = None,
    ) -> CVAnalysis:
        """Run the same skill/metadata extraction used on job postings over
        a candidate's CV text, predict the tech category the candidate best
        fits, and save the resulting analysis (not the raw CV) to disk.
        """
        if not isinstance(cv_text, str) or not cv_text.strip():
            raise ValueError("CV text is empty or unreadable.")

        cleaned = self.clean_text(cv_text)

        skills_by_category = self._skill_extractor.extract_skills(cleaned)
        skills = sorted({s for group in skills_by_category.values() for s in group})
        years_experience = self._skill_extractor.extract_years_experience(cleaned)
        education = self._skill_extractor.extract_education(cleaned)
        certifications = self._skill_extractor.extract_certifications(cleaned)

        seniority = None
        try:
            seniority = self._metadata_extractor.extract_seniority_level("", cleaned).value
        except Exception:  # pragma: no cover - defensive; extraction is best-effort
            logger.debug("Could not infer seniority level from CV text.", exc_info=True)

        predicted_category = None
        prediction_confidence = None
        top_probs: Dict[str, float] = {}
        if self.pipeline is not None:
            prediction = self.predict([cleaned])[0]
            predicted_category = prediction["predicted_tech_category"]
            prediction_confidence = prediction["prediction_confidence"]
            top_probs = prediction["top_category_probabilities"]
        else:
            logger.warning(
                "analyze_cv() called without a trained/loaded model — "
                "skills/metadata were extracted but no category was predicted."
            )

        name = candidate_name.strip() or self._infer_name(cv_text)

        analysis = CVAnalysis(
            cv_id=str(uuid.uuid4()),
            analyzed_at=datetime.now().isoformat(),
            source_filename=source_filename,
            candidate_name=name,
            skills=skills,
            years_experience=years_experience,
            education=education,
            certifications=certifications,
            seniority_level=seniority,
            predicted_tech_category=predicted_category,
            prediction_confidence=prediction_confidence,
            top_category_probabilities=top_probs,
        )

        if save:
            analysis.saved_path = str(self._save_analysis(analysis, output_dir))

        return analysis

    @staticmethod
    def _infer_name(text: str) -> str:
        for line in text.splitlines()[:8]:
            candidate = " ".join(line.strip().split())
            if candidate and "@" not in candidate and 1 < len(candidate) <= 70 and len(candidate.split()) <= 5:
                return candidate.title() if candidate.isupper() else candidate
        return "Candidate"

    @staticmethod
    def _save_analysis(analysis: CVAnalysis, output_dir: Optional[Path] = None) -> Path:
        output_dir = Path(output_dir) if output_dir else ANALYZED_CV_DIR
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = output_dir / f"{timestamp}_{analysis.cv_id}.json"
        with open(out_path, "w", encoding="utf-8") as fh:
            json.dump(analysis.to_dict(), fh, indent=2)
        logger.info("Saved analyzed CV to %s", out_path)
        return out_path


def latest_saved_model(models_dir: Optional[Path] = None) -> Optional[Path]:
    """Convenience helper for a backend: is there already a trained model
    on disk?"""
    models_dir = Path(models_dir) if models_dir else MODELS_DIR
    candidates = sorted(models_dir.glob("tech_category_classifier*.joblib"), key=lambda p: p.stat().st_mtime)
    return candidates[-1] if candidates else None
