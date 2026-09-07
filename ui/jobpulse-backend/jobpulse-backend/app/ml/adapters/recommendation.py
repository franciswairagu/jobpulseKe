"""
Recommendation engine adapter.

This wraps the REAL, uploaded `app.recommender` package as-is - no
retraining, no rewriting of its scoring logic. `JobRecommender` is a
deterministic hybrid weighted scorer (skills 65% / preferred skills
15% / experience 15% / location-workmode 5%, only over components
that have data - see job_recommender.py::_hybrid_score), not a
trained ML model. It is treated as the tested component it is: its
output is used verbatim, never overridden or re-scored here.
"""

from __future__ import annotations

from app.recommender import CandidateProfile, Job as RecommenderJob, JobRecommender
from app.recommender.models import RecommendationResult


class RecommendationEngine:
    """Clean interface required by the integration spec: `recommend(user_profile)`."""

    MODEL_NAME = "job_recommender"
    MODEL_VERSION = "1.0-hybrid-weighted"

    def __init__(self):
        self.engine = JobRecommender()

    def recommend(self, candidate: CandidateProfile, jobs: list[RecommenderJob], top_k: int = 10) -> RecommendationResult:
        return self.engine.build_plan(candidate, jobs, top_k=top_k)
