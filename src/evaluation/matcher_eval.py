"""Skill Matcher evaluation — match/score correctness."""

import logging
from typing import Any, Dict, List

from src.recommender.skills_matcher import SkillMatcher

logger = logging.getLogger(__name__)

# Test cases: (candidate_skills, job_skills, expected_matched, expected_missing, expected_score)
MATCH_TEST_CASES = [
    # Perfect match
    (
        {"python", "django", "postgresql"},
        {"python", "django", "postgresql"},
        {"python", "django", "postgresql"},
        set(),
        1.0,
    ),
    # Partial match
    (
        {"python", "django", "redis"},
        {"python", "django", "postgresql", "redis", "aws"},
        {"python", "django", "redis"},
        {"postgresql", "aws"},
        0.6,
    ),
    # No match
    (
        {"java", "spring"},
        {"python", "django"},
        set(),
        {"python", "django"},
        0.0,
    ),
    # Empty job skills
    (
        {"python", "django"},
        set(),
        set(),
        set(),
        0.0,
    ),
    # Empty candidate skills
    (
        set(),
        {"python", "django"},
        set(),
        {"python", "django"},
        0.0,
    ),
    # Alias resolution: candidate has "golang", job needs "go"
    (
        {"golang", "python"},
        {"go", "python"},
        {"go", "python"},
        set(),
        1.0,
    ),
    # Alias resolution: candidate has "sklearn", job needs "scikit-learn"
    (
        {"sklearn", "pandas"},
        {"scikit-learn", "pandas", "tensorflow"},
        {"scikit-learn", "pandas"},
        {"tensorflow"},
        2 / 3,
    ),
    # Alias resolution: k8s -> kubernetes
    (
        {"docker", "k8s"},
        {"docker", "kubernetes", "terraform"},
        {"docker", "kubernetes"},
        {"terraform"},
        2 / 3,
    ),
]


def evaluate_skill_matcher() -> Dict[str, Any]:
    """Evaluate skill matcher match/score correctness.

    Tests exact set matching, score calculation, and alias resolution
    through the matcher.
    """
    matcher = SkillMatcher()
    correct_matches = 0
    correct_scores = 0
    total = len(MATCH_TEST_CASES)
    failures = []

    for candidate_skills, job_skills, exp_matched, exp_missing, exp_score in MATCH_TEST_CASES:
        matched, missing = matcher.find_matches(candidate_skills, job_skills)
        score = matcher.calculate_score(candidate_skills, job_skills)

        match_ok = matched == exp_matched and missing == exp_missing
        score_ok = abs(score - exp_score) < 0.01

        if match_ok:
            correct_matches += 1
        if score_ok:
            correct_scores += 1

        if not match_ok or not score_ok:
            failures.append({
                "candidate_skills": sorted(candidate_skills),
                "job_skills": sorted(job_skills),
                "expected_matched": sorted(exp_matched),
                "actual_matched": sorted(matched),
                "expected_missing": sorted(exp_missing),
                "actual_missing": sorted(missing),
                "expected_score": round(exp_score, 3),
                "actual_score": round(score, 3),
                "match_correct": match_ok,
                "score_correct": score_ok,
            })

    return {
        "model": "skill_matcher",
        "match_accuracy": round(correct_matches / total, 3) if total else 0,
        "score_accuracy": round(correct_scores / total, 3) if total else 0,
        "correct_matches": correct_matches,
        "correct_scores": correct_scores,
        "total": total,
        "failures": failures,
    }
