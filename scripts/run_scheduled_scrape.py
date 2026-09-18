"""Single, lock-protected scraper run intended for invocation by cron.

Example crontab (every six hours, Nairobi time):
    CRON_TZ=Africa/Nairobi
    0 */6 * * * cd /path/to/jobpulse && /path/to/venv/bin/python scripts/run_scheduled_scrape.py --max-pages 5
"""

import argparse
import logging
import os
import sys
from contextlib import contextmanager
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)

@contextmanager
def exclusive_run_lock():
    """Prevent a slow scrape from overlapping the next scheduled run on Linux."""
    import fcntl

    state_dir = PROJECT_ROOT / ".runtime"
    state_dir.mkdir(exist_ok=True)
    lock_path = state_dir / "scrapers.lock"
    with lock_path.open("w") as lock_file:
        try:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            yield False
            return
        try:
            yield True
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def configure_logging() -> logging.Logger:
    log_dir = PROJECT_ROOT / "logs"
    log_dir.mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.FileHandler(log_dir / "scraper-schedule.log"), logging.StreamHandler()],
    )
    return logging.getLogger("jobpulse.scheduler")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run JobPulse scrapers safely from cron.")
    parser.add_argument("--sources", nargs="+", help="Source names; defaults to the scraper suite's priority list.")
    parser.add_argument("--max-pages", type=int, default=5, help="Per-source page ceiling (default: 5).")
    parser.add_argument("--nlp-batch-size", type=int, default=1000, help="Records per NLP batch (default: 1000).")
    parser.add_argument("--scrape-only", action="store_true", help="Skip stages 1–4; useful for scraper diagnostics.")
    args = parser.parse_args()
    if args.max_pages < 1:
        parser.error("--max-pages must be at least 1")

    # Import after argument parsing: `--help` remains useful before optional
    # scraper dependencies have been installed in a fresh environment.
    from scripts.run_scrapers import RECOMMENDED_PRIORITY, run_sources
    if args.sources:
        unknown_sources = sorted(set(args.sources) - set(RECOMMENDED_PRIORITY))
        if unknown_sources:
            parser.error(f"unknown source(s): {', '.join(unknown_sources)}")

    logger = configure_logging()
    with exclusive_run_lock() as acquired:
        if not acquired:
            logger.warning("Skipped scheduled scrape: another scraper run is still active.")
            return 0
        logger.info("Starting scheduled scrape: sources=%s max_pages=%s", args.sources or "all", args.max_pages)
        try:
            result = run_sources(args.sources or RECOMMENDED_PRIORITY, args.max_pages)
        except Exception:
            logger.exception("Scheduled scrape failed before completion.")
            return 1
        if result is None:
            logger.warning("Scheduled scrape finished with no records; pipeline will not run.")
            return 0
        logger.info("Scheduled scrape finished with %s records.", len(result))
        if args.scrape_only:
            return 0
        # Merge TechMap data into the Africa master before running pipeline
        from scripts.merge_techmap import load_techmap_dir
        from src.config import TECHMAP_DIR
        from src.scraping_config import SCHEMA_COLUMNS
        import pandas as pd
        techmap_csv = PROJECT_ROOT / "data" / "raw" / "techmap_jobs.csv"
        has_techmap = any(TECHMAP_DIR.glob("*.jsonl")) or any(TECHMAP_DIR.glob("*.jsonl.gz"))
        if has_techmap:
            logger.info("Ingesting TechMap data from %s", TECHMAP_DIR)
            records = load_techmap_dir(str(TECHMAP_DIR))
            if records:
                df = pd.DataFrame(records, columns=SCHEMA_COLUMNS)
                df = df.drop_duplicates(subset=["job_id"], keep="first")
                os.makedirs(techmap_csv.parent, exist_ok=True)
                df.to_csv(techmap_csv, index=False)
                logger.info("TechMap: %d records -> %s", len(df), techmap_csv)
        # Merge scrapers + TechMap into Africa master
        master_csv = PROJECT_ROOT / "output" / "master_africa_tech_jobs.csv"
        africa_master = PROJECT_ROOT / "data" / "external" / "jobpulseke_master_africa_tech_jobs.csv"
        frames = []
        if master_csv.exists():
            frames.append(pd.read_csv(master_csv, low_memory=False))
        if techmap_csv.exists():
            frames.append(pd.read_csv(techmap_csv, low_memory=False))
        if frames:
            combined = pd.concat(frames, ignore_index=True)
            combined = combined.drop_duplicates(subset=["job_id"], keep="first")
            os.makedirs(africa_master.parent, exist_ok=True)
            combined.to_csv(africa_master, index=False)
            logger.info("Africa master: %d unique records -> %s", len(combined), africa_master)
        from src.pipeline.full_refresh import run_full_refresh
        outputs = run_full_refresh(africa_master, args.nlp_batch_size)
        logger.info("Full refresh complete: stage4=%s analytics=%s", outputs["stage4"], outputs["analytics"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
