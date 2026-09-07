"""
Evaluation for the Stage 3 NLP pipeline (skill_extractor.py + metadata_extractor.py,
run via nlpv2.py).

There's no human-labeled ground truth for the scraped job postings, so
"evaluate the NLP" here means three complementary checks, each catching a
different failure mode a single accuracy number would hide:

  1. Coverage — over the real enriched dataset, what fraction of records
     actually got a skill/seniority/years-experience/salary extracted?
     Low coverage usually means a description field is empty/too short
     (a data problem) rather than an extractor bug — this check tells
     you which.

  2. Title/seniority consistency — a job_title that literally says
     "Senior ..." should extract to SeniorityLevel.SENIOR. Cheap,
     rule-based cross-check against the extractor's own output using
     signal it didn't structurally have to agree with (title vs.
     description-driven classification) — disagreement rate is a real
     precision proxy without needing hand labels.

  3. Synthetic gold set — a small hand-written set of job description
     snippets with known-correct skills/seniority/years, run through
     the real extractors. Gives an actual precision/recall/F1 number
     for skill extraction and an accuracy number for seniority
     classification, and will catch regressions if the taxonomy or
     rules change later.

Nothing here writes a report file automatically — call
run_evaluation(save=True) if you want data/nlp/evaluation/ populated;
default is print-and-return, consistent with the rest of this pipeline.
"""
import json
import logging
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from src.nlp.skill_extractor import get_extractor
from src.nlp.metadata_extractor import get_metadata_extractor, SeniorityLevel

logger = logging.getLogger(__name__)

TITLE_SENIORITY_HINTS = {
    "intern": SeniorityLevel.INTERN,
    "internship": SeniorityLevel.INTERN,
    "graduate": SeniorityLevel.ENTRY,
    "junior": SeniorityLevel.ENTRY,
    "senior": SeniorityLevel.SENIOR,
    "principal": SeniorityLevel.SENIOR,
    "lead": SeniorityLevel.LEAD,
    "director": SeniorityLevel.EXECUTIVE,
    "vp ": SeniorityLevel.EXECUTIVE,
    "chief": SeniorityLevel.EXECUTIVE,
    "cto": SeniorityLevel.EXECUTIVE,
    "cfo": SeniorityLevel.EXECUTIVE,
}

# ----------------------------------------------------------------------
# 1. Coverage over the real dataset
# ----------------------------------------------------------------------
def evaluate_coverage(df: pd.DataFrame) -> Dict[str, Any]:
    """What fraction of enriched records actually got each field filled in."""
    n = len(df)
    if n == 0:
        return {"records": 0}

    has_skills = (df["skill_count"] > 0).sum()
    has_years = (df["years_experience"] > 0).sum()
    has_salary = df["salary_min_extracted"].notna().sum()
    is_remote = df["is_remote_eligible"].sum()
    empty_description = (df["job_description"].fillna("").str.strip().str.len() < 20).sum()

    return {
        "records": n,
        "skills_found_pct": round(has_skills / n * 100, 1),
        "years_experience_found_pct": round(has_years / n * 100, 1),
        "salary_found_pct": round(has_salary / n * 100, 1),
        "remote_eligible_pct": round(is_remote / n * 100, 1),
        "near_empty_description_pct": round(empty_description / n * 100, 1),
        "note": (
            "near_empty_description_pct is the most useful number here — "
            "low skill/salary coverage is expected (not an extractor bug) "
            "when this is high, since there's no text to extract from."
        ),
    }


# ----------------------------------------------------------------------
# 2. Title vs. extracted-seniority consistency
# ----------------------------------------------------------------------
def evaluate_title_seniority_consistency(df: pd.DataFrame, sample_mismatches: int = 10) -> Dict[str, Any]:
    """For titles with an explicit seniority word, does the extractor's
    seniority_level agree? Only checks records where the title actually
    contains a hint — silent on the (majority of) titles with no signal."""
    checked = 0
    agreed = 0
    mismatches: List[Dict[str, str]] = []

    for _, row in df.iterrows():
        title = str(row.get("job_title") or "").lower()
        expected = None
        for hint, level in TITLE_SENIORITY_HINTS.items():
            if hint in title:
                expected = level
                break
        if expected is None:
            continue

        checked += 1
        actual = row.get("seniority_level")
        if actual == expected.value:
            agreed += 1
        elif len(mismatches) < sample_mismatches:
            mismatches.append({
                "job_title": row.get("job_title"),
                "expected": expected.value,
                "actual": actual,
            })

    return {
        "titles_with_seniority_hint": checked,
        "agreement_pct": round(agreed / checked * 100, 1) if checked else None,
        "sample_mismatches": mismatches,
    }


# ----------------------------------------------------------------------
# 3. Synthetic gold set — precision/recall/F1 for skills, accuracy for
#    seniority, against hand-written examples with known-correct answers.
# ----------------------------------------------------------------------
GOLD_SET = [
    {
        "job_title": "Senior Python Backend Developer",
        "job_description": (
            "We're looking for a Senior Python Developer with 5+ years of experience "
            "building REST APIs with Django and FastAPI. Experience with PostgreSQL, "
            "Redis, and AWS is required. Docker and Kubernetes knowledge is a plus. "
            "Bachelor's degree in Computer Science required."
        ),
        "expected_skills": {"python", "django", "fastapi", "postgresql", "redis", "aws", "docker", "kubernetes"},
        "expected_seniority": SeniorityLevel.SENIOR,
        "expected_years_min": 5,
    },
    {
        "job_title": "Junior Frontend Developer",
        "job_description": (
            "Entry level React developer wanted. You'll work with JavaScript, "
            "TypeScript, and modern CSS. No prior experience required — recent "
            "graduates welcome. Familiarity with Git is helpful."
        ),
        "expected_skills": {"react", "javascript", "typescript", "git"},
        "expected_seniority": SeniorityLevel.ENTRY,
        "expected_years_min": 0,
    },
    {
        "job_title": "DevOps Engineer",
        "job_description": (
            "3+ years experience with Terraform, Kubernetes, and CI/CD pipelines. "
            "Strong knowledge of AWS and Azure required. Experience with "
            "PostgreSQL and MongoDB is a bonus. AWS Certified Solutions Architect preferred."
        ),
        "expected_skills": {"terraform", "kubernetes", "aws", "azure", "postgresql", "mongodb"},
        "expected_seniority": SeniorityLevel.MID,
        "expected_years_min": 3,
    },
    {
        "job_title": "Data Scientist - Machine Learning",
        "job_description": (
            "Lead our ML team building models with TensorFlow and PyTorch. "
            "Strong Python and SQL skills required. Experience with Scikit-learn "
            "and data pipelines. Master's degree in Data Science or related field preferred."
        ),
        "expected_skills": {"tensorflow", "pytorch", "python", "sql", "scikit-learn"},
        "expected_seniority": SeniorityLevel.LEAD,
        "expected_years_min": 0,
    },
    {
        "job_title": "Intern - Software Engineering",
        "job_description": (
            "Summer internship for students. Learn Java and Spring Boot from our "
            "engineering team. No prior professional experience required."
        ),
        "expected_skills": {"java", "spring boot"},
        "expected_seniority": SeniorityLevel.INTERN,
        "expected_years_min": 0,
    },
]


def evaluate_against_gold_set(gold_set: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """Run the real extractors against hand-labeled examples and compute
    precision/recall/F1 (skills) and accuracy (seniority)."""
    gold_set = gold_set or GOLD_SET
    skill_extractor = get_extractor()
    metadata_extractor = get_metadata_extractor()

    per_example = []
    seniority_correct = 0
    total_tp = total_fp = total_fn = 0

    for example in gold_set:
        extracted = skill_extractor.extract_skills(example["job_description"])
        title_extracted = skill_extractor.extract_skills(example["job_title"])
        for cat, skills in title_extracted.items():
            extracted.setdefault(cat, set()).update(skills)
        extracted_flat = {s for skills in extracted.values() for s in skills}

        expected = example["expected_skills"]
        tp = extracted_flat & expected
        fp = extracted_flat - expected
        fn = expected - extracted_flat
        total_tp += len(tp)
        total_fp += len(fp)
        total_fn += len(fn)

        seniority = metadata_extractor.extract_seniority_level(
            example["job_title"], example["job_description"]
        )
        seniority_ok = seniority == example["expected_seniority"]
        seniority_correct += int(seniority_ok)

        per_example.append({
            "job_title": example["job_title"],
            "skills_expected": sorted(expected),
            "skills_extracted": sorted(extracted_flat),
            "skills_missed": sorted(fn),
            "skills_spurious": sorted(fp),
            "seniority_expected": example["expected_seniority"].value,
            "seniority_actual": seniority.value,
            "seniority_correct": seniority_ok,
        })

    precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) else 0.0
    recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0

    return {
        "n_examples": len(gold_set),
        "skill_precision": round(precision, 3),
        "skill_recall": round(recall, 3),
        "skill_f1": round(f1, 3),
        "seniority_accuracy": round(seniority_correct / len(gold_set), 3),
        "per_example": per_example,
    }


# ----------------------------------------------------------------------
# Orchestrator
# ----------------------------------------------------------------------
def run_evaluation(
    nlp_parquet: Optional[Path] = None,
    save: bool = False,
    output_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """Run all three checks and print a readable summary.

    If nlp_parquet is None, auto-detects the latest data/nlp/*.parquet
    output the same way the rest of this pipeline does.
    """
    from src.nlp.nlpv2 import latest_nlp_output  # avoid import cycle at module load

    if nlp_parquet is None:
        nlp_parquet = latest_nlp_output()

    results: Dict[str, Any] = {"timestamp": datetime.now().isoformat()}

    if nlp_parquet is not None and Path(nlp_parquet).exists():
        df = pd.read_parquet(nlp_parquet)
        results["source"] = str(nlp_parquet)
        results["coverage"] = evaluate_coverage(df)
        results["title_seniority_consistency"] = evaluate_title_seniority_consistency(df)
    else:
        logger.warning(
            "No enriched NLP dataset found — skipping coverage/consistency checks "
            "(run src/nlp/nlpv2.py first). Gold-set evaluation will still run."
        )
        results["coverage"] = None
        results["title_seniority_consistency"] = None

    results["gold_set"] = evaluate_against_gold_set()

    _print_report(results)

    if save:
        output_dir = output_dir or (Path(__file__).resolve().parents[2] / "data" / "nlp" / "evaluation")
        output_dir.mkdir(parents=True, exist_ok=True)
        out_path = output_dir / f"nlp_evaluation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(out_path, "w") as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\n✓ Saved evaluation to: {out_path}")

    return results


def _print_report(results: Dict[str, Any]) -> None:
    print("\n" + "=" * 60)
    print("NLP EVALUATION")
    print("=" * 60)

    cov = results.get("coverage")
    if cov:
        print(f"\n[Coverage] over {cov['records']:,} records")
        print(f"  Skills found:          {cov['skills_found_pct']}%")
        print(f"  Years experience found: {cov['years_experience_found_pct']}%")
        print(f"  Salary found:           {cov['salary_found_pct']}%")
        print(f"  Remote-eligible:        {cov['remote_eligible_pct']}%")
        print(f"  Near-empty description: {cov['near_empty_description_pct']}%")

    cons = results.get("title_seniority_consistency")
    if cons and cons["titles_with_seniority_hint"]:
        print(f"\n[Title/Seniority Consistency] {cons['titles_with_seniority_hint']:,} titles had an explicit hint")
        print(f"  Agreement: {cons['agreement_pct']}%")
        if cons["sample_mismatches"]:
            print("  Sample mismatches:")
            for m in cons["sample_mismatches"][:5]:
                print(f"    '{m['job_title']}' -> expected {m['expected']}, got {m['actual']}")

    gold = results["gold_set"]
    print(f"\n[Synthetic Gold Set] {gold['n_examples']} hand-labeled examples")
    print(f"  Skill precision: {gold['skill_precision']}")
    print(f"  Skill recall:    {gold['skill_recall']}")
    print(f"  Skill F1:        {gold['skill_f1']}")
    print(f"  Seniority accuracy: {gold['seniority_accuracy']}")
    for ex in gold["per_example"]:
        if ex["skills_missed"] or ex["skills_spurious"] or not ex["seniority_correct"]:
            print(f"    ⚠ '{ex['job_title']}': missed={ex['skills_missed']}, "
                  f"spurious={ex['skills_spurious']}, "
                  f"seniority={ex['seniority_actual']} (expected {ex['seniority_expected']})")
    print("=" * 60)
