"""Metadata Extractor evaluation — seniority, work mode, employment type accuracy."""

import logging
from collections import Counter
from typing import Any, Dict, List, Optional

from src.nlp.metadata_extractor import SeniorityLevel, get_metadata_extractor

logger = logging.getLogger(__name__)


def evaluate_metadata_extractor(gold_set: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Evaluate metadata extraction against the gold standard.

    Checks three fields:
      - Seniority level (from title + description)
      - Work mode (from description)
      - Employment type (from title + description)

    Returns:
        Per-field accuracy + confusion matrices + per-example detail.
    """
    extractor = get_metadata_extractor()

    seniority_correct = 0
    seniority_total = 0
    work_mode_correct = 0
    work_mode_total = 0
    employment_correct = 0
    employment_total = 0

    seniority_confusion = Counter()
    work_mode_confusion = Counter()
    employment_confusion = Counter()

    per_example = []

    for example in gold_set:
        title = example["job_title"]
        desc = example["job_description"]
        gold_seniority = example["expected_seniority"]
        gold_work_mode = example.get("expected_work_mode")
        gold_employment = example.get("expected_employment_type")

        # Seniority
        pred_seniority = extractor.extract_seniority_level(title, desc)
        s_correct = pred_seniority == gold_seniority
        seniority_correct += int(s_correct)
        seniority_total += 1
        seniority_confusion[(gold_seniority.value, pred_seniority.value)] += 1

        # Work mode
        pred_work_mode = extractor.extract_work_mode(f"{title} {desc}")
        if gold_work_mode is not None:
            wm_correct = pred_work_mode == gold_work_mode
            work_mode_correct += int(wm_correct)
            work_mode_total += 1
            work_mode_confusion[(gold_work_mode, pred_work_mode or "None")] += 1

        # Employment type
        pred_employment = extractor.extract_employment_type(f"{title} {desc}")
        if gold_employment is not None:
            e_correct = pred_employment == gold_employment
            employment_correct += int(e_correct)
            employment_total += 1
            employment_confusion[(gold_employment, pred_employment or "None")] += 1

        per_example.append({
            "job_title": title,
            "seniority_expected": gold_seniority.value,
            "seniority_actual": pred_seniority.value,
            "seniority_correct": s_correct,
            "work_mode_expected": gold_work_mode,
            "work_mode_actual": pred_work_mode,
            "work_mode_correct": wm_correct if gold_work_mode else None,
            "employment_expected": gold_employment,
            "employment_actual": pred_employment,
            "employment_correct": e_correct if gold_employment else None,
        })

    return {
        "model": "metadata_extractor",
        "n_examples": len(gold_set),
        "seniority": {
            "accuracy": round(seniority_correct / seniority_total, 3) if seniority_total else None,
            "correct": seniority_correct,
            "total": seniority_total,
            "confusion": {f"{k[0]}->{k[1]}": v for k, v in seniority_confusion.items()},
        },
        "work_mode": {
            "accuracy": round(work_mode_correct / work_mode_total, 3) if work_mode_total else None,
            "correct": work_mode_correct,
            "total": work_mode_total,
            "confusion": {f"{k[0]}->{k[1]}": v for k, v in work_mode_confusion.items()},
        },
        "employment_type": {
            "accuracy": round(employment_correct / employment_total, 3) if employment_total else None,
            "correct": employment_correct,
            "total": employment_total,
            "confusion": {f"{k[0]}->{k[1]}": v for k, v in employment_confusion.items()},
        },
        "per_example": per_example,
    }
