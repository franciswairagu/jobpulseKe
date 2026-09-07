
"""Backwards-friendly profile entry points."""

from .skill_extractor import profile_from_text
from src.recommender.models import CandidateProfile

__all__ = ["CandidateProfile", "profile_from_text"]
