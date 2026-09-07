"""
NLPAnalysisPipeline
====================

`notebooks/nlp_analysis.ipynb` used to be a sequence of independent,
top-to-bottom cells (load data -> clean text -> extract skills -> extract
metadata -> classify -> topic-model). That's fine for one-off exploration,
but it can't be reused from anywhere else: a backend can't "run cell 14",
and there was nowhere to plug in hyperparameter tuning or CV analysis
without duplicating the same steps.

This class is that whole pipeline, promoted to reusable code. The notebook
now just creates one `NLPAnalysisPipeline`, calls its methods, and plots
whatever it gets back — all the actual logic (and the tunable
classification model) lives here and in `category_classifier.py`.

    from src.nlp.nlp_analysis_pipeline import NLPAnalysisPipeline

    pipeline = NLPAnalysisPipeline()
    pipeline.load_data()
    pipeline.run_data_quality_report()
    pipeline.clean_text_fields()
    pipeline.extract_skills()
    pipeline.extract_metadata()
    tuning_summary = pipeline.train_classifier(tune=True)
    pipeline.save_classifier()                      # -> src/models/*.joblib

    # Anywhere else (a backend, a script, a notebook):
    pipeline.load_classifier()
    analysis = pipeline.analyze_cv(cv_text, source_filename="cv.pdf")
"""
from __future__ import annotations

import logging
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from src.nlp.category_classifier import CVAnalysis, TechCategoryClassifier
from src.nlp.metadata_extractor import get_metadata_extractor
from src.nlp.skill_extractor import get_extractor

logger = logging.getLogger(__name__)


class NLPAnalysisPipeline:
    """End-to-end NLP analysis over JobPulse's cleaned job-postings dataset:
    data-quality auditing, text cleaning, skill/metadata extraction,
    tunable tech-category classification, topic modelling, and CV analysis.
    """

    def __init__(self, data_path: Optional[Path] = None, model_path: Optional[Path] = None):
        self.data_path = data_path
        self.df: Optional[pd.DataFrame] = None
        self.classifier = TechCategoryClassifier(model_path=model_path)
        self._skill_extractor = get_extractor()
        self._metadata_extractor = get_metadata_extractor()

    # ------------------------------------------------------------------
    # 1. Load + data quality
    # ------------------------------------------------------------------
    def load_data(self) -> pd.DataFrame:
        """Load the latest cleaned dataset and run the placeholder-vs-real
        description check + category normalization (delegates to
        TechCategoryClassifier so both stay in sync with what training uses).
        """
        self.df = self.classifier.load_training_data(self.data_path)
        return self.df

    def run_data_quality_report(self) -> Dict[str, Any]:
        """Coverage of REAL (non-placeholder) descriptions, overall and by
        source."""
        self._require_data()
        overall_pct = self.df["has_real_description"].mean() * 100
        coverage_by_source = (
            self.df.groupby("source")["has_real_description"]
            .agg(total="count", real="sum")
        )
        coverage_by_source["pct_real"] = (coverage_by_source["real"] / coverage_by_source["total"] * 100).round(1)
        coverage_by_source = coverage_by_source.sort_values("total", ascending=False)
        return {
            "overall_pct_real": overall_pct,
            "n_real": int(self.df["has_real_description"].sum()),
            "n_total": len(self.df),
            "coverage_by_source": coverage_by_source,
        }

    # ------------------------------------------------------------------
    # 2. Cleaning + skill/metadata extraction (EDA — feeds the classifier
    #    but is also useful on its own, e.g. for the market-analytics side
    #    of this project)
    # ------------------------------------------------------------------
    def clean_text_fields(self) -> pd.DataFrame:
        """`title_clean` / `desc_clean` / `text_for_nlp` are already added
        by `load_data()` (via TechCategoryClassifier.load_training_data);
        this is a no-op re-run kept for notebook clarity/explicitness."""
        self._require_data()
        return self.df

    def extract_skills(self) -> pd.Series:
        self._require_data()

        def _extract(text: str) -> List[str]:
            skills_by_cat = self._skill_extractor.extract_skills(text)
            return sorted({s for skills in skills_by_cat.values() for s in skills})

        self.df["skills_found"] = self.df["text_for_nlp"].apply(_extract)
        self.df["n_skills_found"] = self.df["skills_found"].apply(len)

        real_df = self.df[self.df["has_real_description"]]
        skill_counts = Counter(s for skills in real_df["skills_found"] for s in skills)
        return pd.Series(dict(skill_counts)).sort_values(ascending=False)

    def extract_metadata(self) -> pd.DataFrame:
        self._require_data()
        self.df["employment_type"] = self.df["text_for_nlp"].apply(self._metadata_extractor.extract_employment_type)
        self.df["work_mode"] = self.df["text_for_nlp"].apply(self._metadata_extractor.extract_work_mode)

        def _has_keyword(title: str, description: str) -> bool:
            combined = f"{title} {description}".lower()
            return any(keyword in combined for keyword in self._metadata_extractor.SENIORITY_KEYWORDS)

        self.df["seniority_keyword_found"] = self.df.apply(
            lambda r: _has_keyword(r["title_clean"], r["desc_clean"]), axis=1
        )
        self.df["seniority_level"] = np.where(
            self.df["seniority_keyword_found"],
            self.df.apply(
                lambda r: self._metadata_extractor.extract_seniority_level(r["title_clean"], r["desc_clean"]).value,
                axis=1,
            ),
            "Unspecified",
        )
        return self.df[["employment_type", "work_mode", "seniority_level"]]

    def extract_experience_education(self) -> pd.DataFrame:
        """Returns a REAL-description-only frame with years/education/certs.

        Kept separate from `self.df` (rather than merged back in) because
        these columns only make sense for real-description rows, and the
        pyarrow-backed string columns in `self.df` can't hold the mixed
        list/int values this produces.
        """
        self._require_data()
        real_df = self.df[self.df["has_real_description"]].copy()
        real_df["years_experience"] = real_df["desc_clean"].apply(self._skill_extractor.extract_years_experience)
        real_df["education_required"] = real_df["desc_clean"].apply(self._skill_extractor.extract_education)
        real_df["certifications"] = real_df["desc_clean"].apply(self._skill_extractor.extract_certifications)
        self.experience_df = real_df
        return real_df[["years_experience", "education_required", "certifications"]]

    # ------------------------------------------------------------------
    # 3. Classification — hyperparameter-tuned model + persistence
    # ------------------------------------------------------------------
    def train_classifier(
        self,
        tune: bool = True,
        param_grid: Optional[Dict[str, List[Any]]] = None,
        cv: int = 5,
        min_rows_per_class: int = 8,
        test_size: float = 0.25,
    ) -> Dict[str, Any]:
        """Prepare the modelling dataset and fit the classifier — with
        `GridSearchCV` hyperparameter tuning by default.

        Returns a summary dict (best params/score if tuned, plus a held-out
        evaluation) so the notebook can print/plot it without repeating
        this wiring.
        """
        self._require_data()
        X_train, X_test, y_train, y_test = self.classifier.prepare_dataset(
            self.df, min_rows_per_class=min_rows_per_class, test_size=test_size
        )

        if tune:
            tune_summary = self.classifier.tune(X_train, y_train, param_grid=param_grid, cv=cv)
        else:
            self.classifier.train(X_train, y_train)
            tune_summary = {}

        evaluation = self.classifier.evaluate(X_test, y_test)
        return {
            **tune_summary,
            "evaluation": evaluation,
            "n_train": len(X_train),
            "n_test": len(X_test),
        }

    def save_classifier(self, path: Optional[Path] = None) -> Path:
        return self.classifier.save(path)

    def load_classifier(self, path: Optional[Path] = None) -> TechCategoryClassifier:
        self.classifier = TechCategoryClassifier.load(path)
        return self.classifier

    # ------------------------------------------------------------------
    # 4. Topic modelling
    # ------------------------------------------------------------------
    def topic_model(self, n_topics: int = 6, max_features: int = 1500) -> Dict[int, List[str]]:
        self._require_data()
        from sklearn.decomposition import NMF
        from sklearn.feature_extraction.text import TfidfVectorizer

        real_df = self.df[self.df["has_real_description"]]
        desc_corpus = real_df[real_df["desc_clean"].str.len() > 50]["desc_clean"]

        tfidf = TfidfVectorizer(max_features=max_features, ngram_range=(1, 2), stop_words="english", min_df=2)
        desc_vec = tfidf.fit_transform(desc_corpus)

        nmf = NMF(n_components=n_topics, random_state=42, init="nndsvda", max_iter=500)
        nmf.fit(desc_vec)

        feature_names = tfidf.get_feature_names_out()
        topics = {}
        for topic_idx, topic in enumerate(nmf.components_):
            topics[topic_idx] = [feature_names[i] for i in topic.argsort()[-10:][::-1]]
        return topics

    # ------------------------------------------------------------------
    # 5. CV analysis (delegates to the trained/loaded classifier)
    # ------------------------------------------------------------------
    def analyze_cv(self, cv_text: str, source_filename: Optional[str] = None, save: bool = True) -> CVAnalysis:
        """Analyze a candidate CV with the same extractors + trained
        classifier used on job postings, and persist the analyzed result
        (see `TechCategoryClassifier.analyze_cv` for exactly what's saved
        and why the raw CV text isn't)."""
        return self.classifier.analyze_cv(cv_text, source_filename=source_filename, save=save)

    def _require_data(self) -> None:
        if self.df is None:
            raise RuntimeError("Call load_data() first.")
