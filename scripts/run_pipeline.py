#!/usr/bin/env python3
"""
run_pipeline.py — run the full data pipeline in one command:

    1. Ingest TechMap JSONL -> CSV (if data/techmap/ has files)
    2. Merge scrapers + TechMap into Africa master
    3. Stage 1: Loading & Ingestion
    4. Stage 2: Cleaning & Deduplication
    5. Stage 3: NLP Extraction
    6. Stage 4: Feature Engineering & Analytics

Usage:
    # Full pipeline (scrapers + TechMap + stages 1-4):
    python scripts/run_pipeline.py

    # Skip scrapers, just merge existing data + run stages 1-4:
    python scripts/run_pipeline.py --no-scrape

    # Scrape only, skip pipeline:
    python scripts/run_pipeline.py --scrape-only

    # Dry run (show what would happen):
    python scripts/run_pipeline.py --dry-run
"""
import argparse
import os
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)

from src.config import ANALYTICS_DATA_DIR, PROCESSED_DATA_DIR, TECHMAP_DIR
from src.analytics.stage4_orchestrator import run_stage_4_analytics
from src.ingestion.loader import run_stage_1_ingestion
from src.nlp.nlpv2 import run_nlp_extraction_v2
from src.processing.cleaner import run_stage_2_cleaning

MASTER_CSV = PROJECT_ROOT / "data" / "external" / "jobpulseke_master_africa_tech_jobs.csv"
SCRAPER_MASTER = PROJECT_ROOT / "output" / "master_africa_tech_jobs.csv"
TECHMAP_CSV = PROJECT_ROOT / "data" / "raw" / "techmap_jobs.csv"


def banner(text):
    print(f"\n{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}\n")


def step_scrapers(max_pages):
    banner("STEP 0: RUNNING SCRAPERS")
    from scripts.run_scrapers import run_sources, RECOMMENDED_PRIORITY
    result = run_sources(RECOMMENDED_PRIORITY, max_pages)
    if result is not None:
        print(f"\nScrapers collected {len(result):,} records")
    else:
        print("\nScrapers returned no records")
    return result


def step_merge_techmap():
    banner("STEP 1: INGESTING TECHMAP DATA")
    has_techmap = any(TECHMAP_DIR.glob("*.jsonl")) or any(TECHMAP_DIR.glob("*.jsonl.gz"))
    if not has_techmap:
        print("No TechMap files found, skipping.")
        return

    from scripts.merge_techmap import load_techmap_dir
    import pandas as pd
    from src.scraping_config import SCHEMA_COLUMNS

    records = load_techmap_dir(str(TECHMAP_DIR))
    if not records:
        return
    df = pd.DataFrame(records, columns=SCHEMA_COLUMNS)
    df = df.drop_duplicates(subset=["job_id"], keep="first")
    os.makedirs(TECHMAP_CSV.parent, exist_ok=True)
    df.to_csv(TECHMAP_CSV, index=False)
    print(f"Saved {len(df):,} TechMap records -> {TECHMAP_CSV}")


def step_merge_master():
    banner("STEP 2: BUILDING AFRICA MASTER")
    import pandas as pd
    from src.scraping_config import SCHEMA_COLUMNS

    frames = []
    sources = []

    # Existing master (union so re-runs accumulate instead of overwriting)
    if MASTER_CSV.exists():
        df = pd.read_csv(MASTER_CSV, low_memory=False)
        frames.append(df)
        sources.append(f"existing master: {len(df):,}")

    # Scraper master
    if SCRAPER_MASTER.exists():
        df = pd.read_csv(SCRAPER_MASTER, low_memory=False)
        frames.append(df)
        sources.append(f"scrapers: {len(df):,}")

    # TechMap
    if TECHMAP_CSV.exists():
        df = pd.read_csv(TECHMAP_CSV, low_memory=False)
        frames.append(df)
        sources.append(f"techmap: {len(df):,}")

    if not frames:
        print("No data to merge.")
        return

    combined = pd.concat(frames, ignore_index=True)
    before = len(combined)
    combined = combined.drop_duplicates(subset=["job_id"], keep="first")
    after = len(combined)

    os.makedirs(MASTER_CSV.parent, exist_ok=True)
    combined.to_csv(MASTER_CSV, index=False)

    print(f"Sources: {', '.join(sources)}")
    print(f"Merged: {before:,} -> {after:,} unique ({before - after:,} dupes removed)")
    print(f"Saved -> {MASTER_CSV}")


def step_update_master_full():
    """Union the Africa master into data/processed/master_full.csv.

    master_full.csv is the dataset the backend auto-ingest prefers (it picks
    the candidate with the most rows), so new scrape runs must land here for
    the UI to reflect them. Deduplicated on job_id; existing rows are kept.
    """
    banner("STEP 2b: UPDATING master_full.csv")
    import pandas as pd

    master_full = PROCESSED_DATA_DIR / "master_full.csv"
    if not MASTER_CSV.exists():
        print("No Africa master found, skipping.")
        return

    new_df = pd.read_csv(MASTER_CSV, low_memory=False)
    if master_full.exists():
        old_df = pd.read_csv(master_full, low_memory=False)
        combined = pd.concat([old_df, new_df], ignore_index=True)
        before = len(combined)
        combined = combined.drop_duplicates(subset=["job_id"], keep="first")
        after = len(combined)
        print(f"Union: {len(old_df):,} existing + {len(new_df):,} new "
              f"-> {before:,} rows -> {after:,} unique ({before - after:,} dupes removed)")
    else:
        combined = new_df
        after = len(combined)
        print(f"master_full.csv missing — seeded with {after:,} rows")

    combined.to_csv(master_full, index=False)
    print(f"Saved -> {master_full}")


def step_stage1():
    banner("STAGE 1: DATA LOADING & INGESTION")
    _, summary = run_stage_1_ingestion(str(MASTER_CSV))
    latest = max(PROCESSED_DATA_DIR.glob("ingested_raw_*.parquet"), key=lambda p: p.stat().st_mtime)
    marker = PROCESSED_DATA_DIR / ".last_stage1_output"
    marker.write_text(str(latest))
    print(f"\nStage 1 complete: {summary['total_records_ingested']:,} records -> {latest}")
    return latest


def step_stage2(stage1_output):
    banner("STAGE 2: CLEANING & DEDUPLICATION")
    _, _, stage2_output = run_stage_2_cleaning(str(stage1_output))
    print(f"\nStage 2 complete -> {stage2_output}")
    return stage2_output


def step_stage3(stage2_output, batch_size):
    banner("STAGE 3: NLP EXTRACTION")
    _, summary = run_nlp_extraction_v2(Path(stage2_output), batch_size=batch_size)
    stage3_output = Path(summary["output"]["path"])
    print(f"\nStage 3 complete -> {stage3_output}")
    return stage3_output


def step_stage4(stage3_output, run_id):
    banner("STAGE 4: FEATURE ENGINEERING & ANALYTICS")
    stage4_output = PROCESSED_DATA_DIR / f"jobpulse_features_{run_id}.parquet"
    analytics_dir = ANALYTICS_DATA_DIR / f"refresh_{run_id}"
    run_stage_4_analytics(stage3_output, stage4_output, analytics_dir)
    print(f"\nStage 4 complete -> {stage4_output}")
    print(f"Analytics     -> {analytics_dir}")
    return stage4_output, analytics_dir


def main():
    parser = argparse.ArgumentParser(description="Run the full JobPulse data pipeline")
    parser.add_argument("--no-scrape", action="store_true", help="Skip scrapers, use existing CSVs")
    parser.add_argument("--scrape-only", action="store_true", help="Run scrapers only, skip stages 1-4")
    parser.add_argument("--max-pages", type=int, default=15, help="Per-scraper page cap (default: 15)")
    parser.add_argument("--nlp-batch-size", type=int, default=1000, help="NLP batch size (default: 1000)")
    parser.add_argument("--dry-run", action="store_true", help="Show plan without executing")
    args = parser.parse_args()

    start = time.time()
    run_id = time.strftime("%Y%m%d_%H%M%S")

    if args.dry_run:
        banner("DRY RUN — PLAN")
        print("Steps that would run:")
        if not args.no_scrape:
            print("  0. Run all scrapers")
        print(f"  1. Ingest TechMap from {TECHMAP_DIR}")
        print(f"  2. Merge into {MASTER_CSV}")
        print(f"  3. Stage 1 -> ingested_raw_{run_id}.parquet")
        print(f"  4. Stage 2 -> jobpulse_cleaned_{run_id}.parquet")
        print(f"  5. Stage 3 -> jobs_nlp_enriched_{run_id}.parquet")
        print(f"  6. Stage 4 -> jobpulse_features_{run_id}.parquet + analytics/")
        return

    banner(f"JOBPULSE PIPELINE — {run_id}")

    # Step 0: Scrapers
    if not args.no_scrape:
        step_scrapers(args.max_pages)

    if args.scrape_only:
        print("\nScrape-only mode, skipping pipeline stages.")
        return

    # Merge
    step_merge_techmap()
    step_merge_master()
    step_update_master_full()

    # Stages 1-4
    stage1_out = step_stage1()
    stage2_out = step_stage2(stage1_out)
    stage3_out = step_stage3(stage2_out, args.nlp_batch_size)
    stage4_out, analytics_dir = step_stage4(stage3_out, run_id)

    elapsed = time.time() - start
    banner(f"PIPELINE COMPLETE ({elapsed:.0f}s)")
    print(f"  Master:    {MASTER_CSV}")
    print(f"  Features:  {stage4_out}")
    print(f"  Analytics: {analytics_dir}")


if __name__ == "__main__":
    main()
