"""Skill Normalizer evaluation — alias resolution accuracy."""

import logging
from typing import Any, Dict, List

from src.recommender.skill_normalizer import SKILL_ALIASES, SkillNormalizer

logger = logging.getLogger(__name__)

# Test cases: (input, expected_canonical)
TEST_CASES = [
    # All aliases from SKILL_ALIASES
    ("golang", "go"),
    ("csharp", "c#"),
    ("nextjs", "next.js"),
    ("aspnet", "asp.net"),
    ("postgres", "postgresql"),
    ("amazon web services", "aws"),
    ("google cloud", "gcp"),
    ("microsoft azure", "azure"),
    ("sklearn", "scikit-learn"),
    ("k8s", "kubernetes"),
    ("cicd", "ci/cd"),
    ("hugging face", "huggingface"),
    ("powerbi", "power bi"),
    # Already canonical — should pass through unchanged
    ("python", "python"),
    ("javascript", "javascript"),
    ("docker", "docker"),
    ("react", "react"),
    ("sql", "sql"),
    # Edge cases: casing, whitespace
    ("Python", "python"),
    ("  GOLANG  ", "go"),
    ("CSharp", "c#"),
    ("  k8s  ", "kubernetes"),
    ("SQL", "sql"),
    ("Docker", "docker"),
    # Unknown skills — should pass through unchanged
    ("obscure_skill", "obscure_skill"),
    ("my_custom_lib", "my_custom_lib"),
]


def evaluate_skill_normalizer() -> Dict[str, Any]:
    """Evaluate skill normalizer alias resolution accuracy.

    Tests all aliases in SKILL_ALIASES plus edge cases (casing, whitespace,
    unknown skills).
    """
    normalizer = SkillNormalizer()
    correct = 0
    total = len(TEST_CASES)
    failures = []

    for input_skill, expected in TEST_CASES:
        actual = normalizer.normalize(input_skill)
        if actual == expected:
            correct += 1
        else:
            failures.append({
                "input": input_skill,
                "expected": expected,
                "actual": actual,
            })

    # Also test normalize_many
    test_batch = ["golang", "Python", "  k8s  ", "sklearn", "unknown"]
    expected_batch = {"go", "python", "kubernetes", "scikit-learn", "unknown"}
    actual_batch = normalizer.normalize_many(test_batch)
    batch_correct = actual_batch == expected_batch

    return {
        "model": "skill_normalizer",
        "accuracy": round(correct / total, 3) if total else 0,
        "correct": correct,
        "total": total,
        "batch_normalize_correct": batch_correct,
        "failures": failures,
        "alias_count": len(SKILL_ALIASES),
    }
