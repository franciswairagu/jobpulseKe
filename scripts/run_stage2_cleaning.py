#!/usr/bin/env python3
"""
JobPulse - Stage 2: Data Cleaning, Geo-Normalization & Deduplication

Run from anywhere with:
    python scripts/run_stage2_cleaning.py
"""
import sys
from pathlib import Path

# Project root (two levels up: scripts/ -> project root) so `src.*`
# absolute imports resolve regardless of the current working directory.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import PROCESSED_DATA_DIR
from src.processing.cleaner import run_stage_2_cleaning

LAST_RUN_MARKER = PROCESSED_DATA_DIR / ".last_stage1_output"


def latest_ingested_parquet():
    """Find the Stage 1 output to clean.

    Prefer the marker file Stage 1 just wrote (so Stage 2 always cleans
    exactly what was just ingested), and fall back to the most recently
    modified ingested_raw_*.parquet on disk if no marker is present.
    """
    if LAST_RUN_MARKER.exists():
        marked = Path(LAST_RUN_MARKER.read_text().strip())
        if marked.exists():
            return marked

    candidates = sorted(
        PROCESSED_DATA_DIR.glob("ingested_raw_*.parquet"),
        key=lambda p: p.stat().st_mtime,
    )
    return candidates[-1] if candidates else None


def main():
    """Run Stage 2: Data Cleaning"""

    input_parquet = latest_ingested_parquet()

    if input_parquet is None:
        print(f"Error: No Stage 1 output found in {PROCESSED_DATA_DIR}. "
              f"Run scripts/run_stage1_ingestion.py first.")
        sys.exit(1)

    print(f"Using Stage 1 output: {input_parquet}")

    # Run cleaning pipeline
    df, report, output_path = run_stage_2_cleaning(str(input_parquet))

    print(f"\n✓ Cleaned dataset saved to: {output_path}")
    print(f"  Records: {len(df):,} "
          f"(reduction rate: {report['output']['reduction_rate']:.2f}%)")

    return df


if __name__ == "__main__":
    main()
