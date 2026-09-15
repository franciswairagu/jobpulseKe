#!/usr/bin/env python3
"""
JobPulse - Stage 4: Feature Engineering & Analytics Aggregations

Run from anywhere with:
    python scripts/run_stage4_analytics.py
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import PROCESSED_DATA_DIR, NLP_DATA_DIR, ANALYTICS_DATA_DIR
from src.analytics.stage4_orchestrator import run_stage_4_analytics

LAST_NLP_MARKER = PROCESSED_DATA_DIR / ".last_nlp_output"


def latest_nlp_parquet():
    """Find the Stage 3 output to process.

    Prefer the marker file Stage 3 wrote, fall back to the most recently
    modified jobs_nlp_enriched_*.parquet on disk.
    """
    if LAST_NLP_MARKER.exists():
        marked = Path(LAST_NLP_MARKER.read_text().strip())
        if marked.exists():
            return marked

    candidates = sorted(
        NLP_DATA_DIR.glob("jobs_nlp_enriched_*.parquet"),
        key=lambda p: p.stat().st_mtime,
    )
    return candidates[-1] if candidates else None


def main():
    """Run Stage 4: Feature Engineering & Analytics Aggregations"""

    input_parquet = latest_nlp_parquet()

    if input_parquet is None:
        print(f"Error: No Stage 3 output found in {NLP_DATA_DIR}. "
              f"Run scripts/run_nlp_extraction.py first.")
        sys.exit(1)

    print(f"Using Stage 3 output: {input_parquet}")

    # Output paths
    features_parquet = PROCESSED_DATA_DIR / "jobpulse_features.parquet"
    analytics_dir = ANALYTICS_DATA_DIR / f"refresh_{Path(input_parquet).stem.split('_')[-1]}"

    # Run analytics pipeline
    summary = run_stage_4_analytics(input_parquet, features_parquet, analytics_dir)

    print(f"\n✓ Feature-engineered dataset: {features_parquet}")
    print(f"✓ Analytics exports: {analytics_dir}/")
    print(f"  Aggregations: skill_region_matrix, salary_distribution, "
          f"remote_trends, career_pathways, skills_by_seniority")


if __name__ == "__main__":
    main()
