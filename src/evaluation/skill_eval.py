"""Skill Extractor evaluation — precision, recall, F1, per-category breakdown."""

import logging
from collections import Counter, defaultdict
from typing import Any, Dict, List

from src.nlp.skill_extractor import get_extractor

logger = logging.getLogger(__name__)


def evaluate_skill_extractor(gold_set: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Evaluate skill extraction against the gold standard.

    For each example, runs the extractor on title + description, then
    computes precision/recall/F1 against expected_skills.

    Returns:
        Aggregate metrics + per-example detail + category breakdown.
    """
    extractor = get_extractor()

    total_tp = total_fp = total_fn = 0
    per_example = []
    category_stats = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0})
    all_missed = Counter()
    all_spurious = Counter()

    for example in gold_set:
        title = example["job_title"]
        desc = example["job_description"]
        text = f"{title} {desc}"
        expected = example["expected_skills"]

        # Extract skills
        extracted = extractor.extract_skills(text)
        extracted_flat = {s for skills in extracted.values() for s in skills}

        # Also extract from title alone (some skills only appear there)
        title_extracted = extractor.extract_skills(title)
        for cat, skills in title_extracted.items():
            extracted.setdefault(cat, set()).update(skills)
        extracted_flat = {s for skills in extracted.values() for s in skills}

        tp = extracted_flat & expected
        fp = extracted_flat - expected
        fn = expected - extracted_flat

        total_tp += len(tp)
        total_fp += len(fp)
        total_fn += len(fn)

        # Per-category tracking
        skill_to_cat = {}
        for cat, skills in extracted.items():
            for s in skills:
                skill_to_cat[s] = cat

        for s in tp:
            cat = skill_to_cat.get(s, "unknown")
            category_stats[cat]["tp"] += 1
        for s in fp:
            cat = skill_to_cat.get(s, "unknown")
            category_stats[cat]["fp"] += 1
            all_spurious[s] += 1
        for s in fn:
            all_missed[s] += 1

        per_example.append({
            "job_title": title,
            "expected_count": len(expected),
            "extracted_count": len(extracted_flat),
            "tp": len(tp),
            "fp": len(fp),
            "fn": len(fn),
            "precision": round(len(tp) / (len(tp) + len(fp)), 3) if (tp or fp) else 1.0,
            "recall": round(len(tp) / (len(tp) + len(fn)), 3) if (tp or fn) else 1.0,
            "skills_missed": sorted(fn),
            "skills_spurious": sorted(fp),
        })

    precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) else 0.0
    recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0

    # Category-level F1
    category_f1 = {}
    for cat, stats in category_stats.items():
        cat_p = stats["tp"] / (stats["tp"] + stats["fp"]) if (stats["tp"] + stats["fp"]) else 0.0
        cat_r = stats["tp"] / (stats["tp"] + stats["fn"]) if (stats["tp"] + stats["fn"]) else 0.0
        cat_f1 = 2 * cat_p * cat_r / (cat_p + cat_r) if (cat_p + cat_r) else 0.0
        category_f1[cat] = {
            "precision": round(cat_p, 3),
            "recall": round(cat_r, 3),
            "f1": round(cat_f1, 3),
            "support": stats["tp"] + stats["fn"],
        }

    return {
        "model": "skill_extractor",
        "n_examples": len(gold_set),
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": round(f1, 3),
        "total_tp": total_tp,
        "total_fp": total_fp,
        "total_fn": total_fn,
        "top_missed_skills": all_missed.most_common(10),
        "top_spurious_skills": all_spurious.most_common(10),
        "category_f1": category_f1,
        "per_example": per_example,
    }
