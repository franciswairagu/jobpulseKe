#!/usr/bin/env python3
"""
JobPulse - Stage 2: Data Cleaning, Geo-Normalization & Deduplication
"""
import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent / "src"))

from config import REPORTS_DIR, PROCESSED_DATA_DIR
from processing.cleaner import run_stage_2_cleaning

LAST_RUN_MARKER = PROCESSED_DATA_DIR / ".last_stage1_output"


def latest_ingested_parquet():
    """Find the Stage 1 output to clean.

    Previously this was a hardcoded filename (e.g.
    ingested_raw_20260831_080646.parquet), which broke every time Stage 1
    was re-run and produced a new timestamp. Now: prefer the marker file
    Stage 1 just wrote (so Stage 2 always cleans exactly what was just
    ingested), and fall back to the most recently modified
    ingested_raw_*.parquet on disk if no marker is present.
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
        print(f"Error: No Stage 1 output found in {PROCESSED_DATA_DIR}. Run run_stage1.py first.")
        sys.exit(1)

    print(f"Using Stage 1 output: {input_parquet}")

    # Run cleaning pipeline
    df, report, output_path = run_stage_2_cleaning(str(input_parquet))

    # Save report
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS_DIR / f"stage2_cleaning_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)

    print(f"\n✓ Report saved to: {report_path}")
    return df


if __name__ == "__main__":
    main()
