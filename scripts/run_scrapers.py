"""
Orchestrator for the Africa Tech Jobs scraper suite.

Usage:
    python scripts/run_scrapers.py                          # run every scraper
    python scripts/run_scrapers.py --sources brightermonday fuzu --max-pages 5
    python scripts/run_scrapers.py --list                   # show available source names

Each scraper's raw output is saved individually to output/<source>.csv
AND merged into output/master_africa_tech_jobs.csv (deduplicated on
job_id, which is a hash of source + source_job_id/url).
"""
import argparse
import os
import sys
from pathlib import Path

import pandas as pd

# Project root (two levels up: scripts/ -> project root) so `src.*`
# absolute imports resolve regardless of the current working directory.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.scraping_config import SCHEMA_COLUMNS, OUTPUT_DIR
from src.collectors.brightermonday import BrighterMondayScraper
from src.collectors.fuzu import FuzuScraper
from src.collectors.myjobmag import MyJobMagScraper
from src.collectors.jobberman import JobbermanScraper
from src.collectors.jobwebkenya import JobWebKenyaScraper
from src.collectors.remoteok import RemoteOKScraper
from src.collectors.weworkremotely import WeWorkRemotelyScraper
from src.collectors.careerjet import CareerJetScraper
from src.collectors.linkedin_guest import LinkedInGuestScraper
from src.collectors.indeed import IndeedScraper
from src.collectors.jobicy import JobicyScraper
from src.collectors.careers24 import Careers24Scraper
from src.collectors.pnet import PNetScraper
from src.collectors.talent_com import TalentComScraper
from src.collectors.hotnigerianjobs import HotNigerianJobsScraper

SCRAPER_REGISTRY = {
    "brightermonday": BrighterMondayScraper,
    "fuzu": FuzuScraper,
    "myjobmag": MyJobMagScraper,
    "jobberman": JobbermanScraper,
    "jobwebkenya": JobWebKenyaScraper,
    "remoteok": RemoteOKScraper,
    "weworkremotely": WeWorkRemotelyScraper,
    "careerjet": CareerJetScraper,
    "linkedin": LinkedInGuestScraper,
    "indeed": IndeedScraper,
    "jobicy": JobicyScraper,
    "careers24": Careers24Scraper,
    "pnet": PNetScraper,
    "talent_com": TalentComScraper,
    "hotnigerianjobs": HotNigerianJobsScraper,
}

# Priority order, updated based on real run results across the whole
# project so far:
# - remoteok/weworkremotely/jobicy: API/RSS, most reliable
# - talent_com: aggregator, high volume potential, structure verified live
# - hotnigerianjobs: structure verified live via direct fetch,
#   832 active postings on ONE Nigerian board's tech-industry page alone
# - linkedin: worked last run (429-limited but got real records)
# - myjobmag/jobwebkenya/brightermonday/fuzu/jobberman: rewritten v2,
#   anchor-first fallback
# - careerjet/careers24/pnet: unverified structure, lowest confidence
#   of the HTML scrapers
# - indeed: last, heaviest anti-bot
RECOMMENDED_PRIORITY = [
    "remoteok", "weworkremotely", "jobicy",
    "talent_com", "hotnigerianjobs",
    "linkedin",
    "myjobmag", "jobwebkenya",
    "brightermonday", "fuzu", "jobberman",
    "careerjet", "careers24", "pnet",
    "indeed",
]


def run_sources(source_names, max_pages):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    all_frames = []

    for name in source_names:
        cls = SCRAPER_REGISTRY.get(name)
        if not cls:
            print(f"[skip] unknown source '{name}'")
            continue

        print(f"\n=== Running {name} ===")
        scraper = cls()
        try:
            records = scraper.scrape(max_pages=max_pages)
        except Exception as e:
            print(f"[error] {name} crashed: {e}")
            print(f"        (continuing with remaining sources)")
            continue

        df = pd.DataFrame(records, columns=SCHEMA_COLUMNS)
        out_path = os.path.join(OUTPUT_DIR, f"{name}.csv")
        df.to_csv(out_path, index=False)
        print(f"[ok] {name}: {len(df)} records -> {out_path}")
        if len(df) == 0:
            print(f"     0 records — check output/debug/{name}_*.html to see what the site actually returned")
        all_frames.append(df)

    if not all_frames:
        print("\nNo records scraped from any source.")
        return None

    master = pd.concat(all_frames, ignore_index=True)
    before = len(master)
    master = master.drop_duplicates(subset=["job_id"], keep="first")
    after = len(master)

    master_path = os.path.join(OUTPUT_DIR, "master_africa_tech_jobs.csv")
    master.to_csv(master_path, index=False)
    print(f"\n=== Master dataset: {after} records ({before - after} duplicates dropped) ===")
    print(f"Saved -> {master_path}")
    return master


def main():
    parser = argparse.ArgumentParser(description="Africa Tech Jobs scraper suite")
    parser.add_argument(
        "--sources", nargs="+", default=None,
        help="Which sources to run (default: all, in recommended priority order)",
    )
    parser.add_argument(
        "--max-pages", type=int, default=15,
        help=(
            "Max pages/passes per search term per site (default: 15). "
            "Each scraper auto-stops earlier if a site runs out of "
            "results before that, so this is a ceiling, not a target — "
            "safe to set higher (e.g. 40) for max coverage."
        ),
    )
    parser.add_argument(
        "--list", action="store_true", help="List available source names and exit",
    )
    args = parser.parse_args()

    if args.list:
        print("Available sources:")
        for name in RECOMMENDED_PRIORITY:
            print(f"  - {name}")
        sys.exit(0)

    sources = args.sources or RECOMMENDED_PRIORITY
    run_sources(sources, args.max_pages)


if __name__ == "__main__":
    main()
