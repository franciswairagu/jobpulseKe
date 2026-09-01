#!/usr/bin/env python3
"""
JobPulse - African Tech Job Market Intelligence Platform
Stage 1 Entry Point
"""
import sys
from pathlib import Path
import json
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from config import REPORTS_DIR, PROCESSED_DATA_DIR
from ingestion import run_stage_1_ingestion

# Source CSV: the merged master dataset produced by the jobpulseKe project
# (africa_tech_jobs_scraper's live-scraped sources + jobpulseKe's
# Kenya-specific myjobmag/fuzu/brightermonday/jobicy/remotive scrapers,
# merged via jobpulseKe's merge_jobpulseke.py). A copy is kept under
# data/external/ so this project doesn't depend on the sibling jobpulseKe
# checkout being present on disk at run time -- re-copy it there whenever
# jobpulseKe produces a fresh master.
JOBPULSEKE_MASTER_CSV = (
    Path(__file__).parent / "data" / "external" / "jobpulseke_master_africa_tech_jobs.csv"
)

# Stage 2 needs to know which Parquet file this run just produced.
# run_stage_1_ingestion() doesn't return that path directly (only a
# summary dict), so we snapshot the directory before/after and record
# the result here for run_stage2.py to pick up automatically instead of
# a hardcoded filename.
LAST_RUN_MARKER = PROCESSED_DATA_DIR / ".last_stage1_output"


def main():
    """Run Stage 1: Data Loading & Ingestion"""

    if not JOBPULSEKE_MASTER_CSV.exists():
        print(f"Error: Input file not found: {JOBPULSEKE_MASTER_CSV}")
        print("  (expected the jobpulseKe project's data/raw/master_africa_tech_jobs.csv, "
              "copied to data/external/jobpulseke_master_africa_tech_jobs.csv)")
        sys.exit(1)

    existing_parquets = set(PROCESSED_DATA_DIR.glob("ingested_raw_*.parquet"))

    # Run ingestion against jobpulseKe's merged master CSV
    df, summary = run_stage_1_ingestion(str(JOBPULSEKE_MASTER_CSV))

    # Determine which parquet file this run just wrote
    new_parquets = sorted(
        set(PROCESSED_DATA_DIR.glob("ingested_raw_*.parquet")) - existing_parquets,
        key=lambda p: p.stat().st_mtime,
    )
    if new_parquets:
        parquet_path = new_parquets[-1]
    else:
        # Fallback: same-second write collided with an existing file, or
        # this is a re-run -- just take the most recently modified one.
        parquet_path = max(
            PROCESSED_DATA_DIR.glob("ingested_raw_*.parquet"),
            key=lambda p: p.stat().st_mtime,
        )
    LAST_RUN_MARKER.write_text(str(parquet_path))
    print(f"✓ Ingested Parquet: {parquet_path}")

    # Save report
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS_DIR / f"stage1_ingestion_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    with open(report_path, 'w') as f:
        # Convert non-serializable types
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "stage": "Stage 1: Data Ingestion",
            "source_csv": str(JOBPULSEKE_MASTER_CSV),
            "output_parquet": str(parquet_path),
            "summary": summary,
        }
        json.dump(report_data, f, indent=2, default=str)

    print(f"\n✓ Report saved to: {report_path}")
    return df


if __name__ == "__main__":
    main()
