"""
merge_jobpulseke.py — pull the collected Kenya tech-jobs dataset from the
sister "jobpulseKe" project into this project's canonical schema
(src.scraping_config.SCHEMA_COLUMNS) and merge it into master_africa_tech_jobs.csv,
the same way merge_csvs.py merges any other schema-conformant CSV.

WHY A DEDICATED SCRIPT (instead of just running merge_csvs.py on the raw
file): jobpulseKe's output is *schema-compatible but not schema-identical*:

  1. Extra column `remote_eligible` (0/1 flag) that doesn't exist here —
     dropped (remote_scope already carries the richer version of this).
  2. `source` values are capitalized ("MyJobMag", "BrighterMonday",
     "Fuzu", "Jobicy", "Remotive") where every scraper in this project
     uses lowercase, unspaced source tags ("myjobmag", "brightermonday",
     ...). Left as-is, dedup against this project's own myjobmag/fuzu/
     brightermonday/jobicy rows would silently fail (different job_id
     hash input) and you'd double-count the same postings under two
     source labels.
  3. `job_id` there is `sha256(url)`, NOT this project's
     `sha256(f"{source}|{source_job_id or url}")` (see
     src.utils.helpers.make_job_id). Different hash scheme -> even a truly
     identical posting would get a different job_id and dedup would
     miss it. Every row is re-hashed here with the same function this
     project's own scrapers use, so cross-project duplicates collapse
     correctly and the merge is safe to re-run.
  4. `work_mode` there uses "On-site" (unset for ~78% of rows); this
     project's schema expects the lowercase set in src.scraping_config.WORK_MODES
     ("remote"/"hybrid"/"onsite"/"unknown"). Existing values are
     normalized, and any missing/unknown value is backfilled with
     src.utils.helpers.guess_work_mode() from the title/description/location
     text, same as every scraper here already does.

Usage:
    # default: read data/external/jobpulseke/kenya_tech_jobs_master.csv,
    # merge into data/raw/master_africa_tech_jobs.csv
    python scripts/merge_jobpulseke.py

    # point at a different jobpulseKe export, or a different master:
    python scripts/merge_jobpulseke.py --input path/to/kenya_tech_jobs_master.csv \
        --master data/raw/master_africa_tech_jobs.csv

    # just see what would happen, don't write anything:
    python scripts/merge_jobpulseke.py --dry-run
"""
import argparse
import os
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.scraping_config import SCHEMA_COLUMNS, WORK_MODES
from src.utils.helpers import (
    make_job_id, clean_text, guess_work_mode, guess_country,
    classify_tech_category, guess_currency, clean_salary, now_iso,
)

DEFAULT_INPUT = os.path.join(
    "data", "external", "jobpulseke", "kenya_tech_jobs_master.csv"
)
DEFAULT_MASTER = os.path.join("data", "raw", "master_africa_tech_jobs.csv")

# jobpulseKe's `source` values -> this project's lowercase source tags.
# Keys are matched case-insensitively. Anything not listed here is just
# lowercased, so new/unseen sources still merge sanely instead of
# erroring out.
SOURCE_NAME_MAP = {
    "myjobmag": "myjobmag",
    "fuzu": "fuzu",
    "brightermonday": "brightermonday",
    "jobicy": "jobicy",
    "remotive": "remotive",
}

# jobpulseKe's work_mode spellings -> src.scraping_config.WORK_MODES
WORK_MODE_MAP = {
    "remote": "remote",
    "hybrid": "hybrid",
    "on-site": "onsite",
    "onsite": "onsite",
    "on site": "onsite",
}


def _s(value):
    """NaN/float-safe wrapper around clean_text (pandas gives back NaN,
    a float, for empty cells — clean_text expects a string or None)."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    return clean_text(str(value))


def normalize_source(raw_source):
    key = _s(raw_source)
    if not key:
        return "jobpulseke"
    return SOURCE_NAME_MAP.get(key.lower(), key.lower().replace(" ", "_"))


def normalize_work_mode(raw_mode, text_blobs):
    key = _s(raw_mode)
    if key:
        mapped = WORK_MODE_MAP.get(key.lower())
        if mapped:
            return mapped
    # fall back to the same free-text guesser every scraper here uses
    return guess_work_mode(text_blobs)


def load_jobpulseke(path):
    df = pd.read_csv(path, low_memory=False)
    print(f"[ok] loaded {len(df):,} rows from {path}")

    # 1. drop columns this schema doesn't have (e.g. remote_eligible),
    #    add any this schema needs that jobpulseKe doesn't carry
    for col in SCHEMA_COLUMNS:
        if col not in df.columns:
            df[col] = None
    extra = [c for c in df.columns if c not in SCHEMA_COLUMNS]
    if extra:
        print(f"[info] dropping columns not in this project's schema: {extra}")
    df = df[SCHEMA_COLUMNS].copy()

    records = []
    for row in df.to_dict(orient="records"):
        source = normalize_source(row.get("source"))
        job_title = _s(row.get("job_title"))
        job_description = _s(row.get("job_description"))
        location = _s(row.get("location"))
        vacancy_url = _s(row.get("vacancy_url"))
        source_job_id = _s(row.get("source_job_id")) or None

        text_blobs = [job_title, job_description, location]

        country = _s(row.get("country")) or guess_country(text_blobs)
        work_mode = normalize_work_mode(row.get("work_mode"), text_blobs)
        if work_mode not in WORK_MODES:
            work_mode = "unknown"
        tech_category = (
            _s(row.get("tech_category"))
            or classify_tech_category(text_blobs)
        )
        salary = clean_salary(_s(row.get("salary")))
        currency = _s(row.get("currency")) or guess_currency(salary)
        scraped_at = _s(row.get("scraped_at")) or now_iso()

        # Re-hash with THIS project's scheme (source + source_job_id/url)
        # so cross-project duplicates of the same posting collapse
        # correctly instead of silently double-counting.
        job_id = make_job_id(source, source_job_id, vacancy_url)

        records.append({
            "job_id": job_id,
            "source": source,
            "source_job_id": source_job_id,
            "job_title": job_title,
            "company": _s(row.get("company")),
            "job_description": job_description,
            "location": location,
            "country": country,
            "work_mode": work_mode,
            "remote_scope": _s(row.get("remote_scope")),
            "job_field": _s(row.get("job_field")),
            "industry": _s(row.get("industry")),
            "employment_type": _s(row.get("employment_type")),
            "experience_required": _s(row.get("experience_required")),
            "education_required": _s(row.get("education_required")),
            "salary": salary,
            "currency": currency,
            "date_posted": _s(row.get("date_posted")),
            "application_deadline": _s(row.get("application_deadline")),
            "tech_category": tech_category,
            "vacancy_url": vacancy_url,
            "scraped_at": scraped_at,
        })

    out = pd.DataFrame(records, columns=SCHEMA_COLUMNS)
    before = len(out)
    out = out.drop_duplicates(subset=["job_id"], keep="first")
    if before != len(out):
        print(f"[info] {before - len(out)} duplicate rows within jobpulseKe's own export dropped")
    return out


def load_master(path):
    if not os.path.exists(path):
        print(f"[info] no existing master at {path} — will create it")
        return pd.DataFrame(columns=SCHEMA_COLUMNS)
    df = pd.read_csv(path, low_memory=False)
    missing = [c for c in SCHEMA_COLUMNS if c not in df.columns]
    for c in missing:
        df[c] = None
    return df[SCHEMA_COLUMNS]


def main():
    parser = argparse.ArgumentParser(
        description="Merge jobpulseKe's Kenya tech-jobs dataset into master_africa_tech_jobs.csv"
    )
    parser.add_argument("--input", default=DEFAULT_INPUT,
                         help=f"jobpulseKe export CSV (default: {DEFAULT_INPUT})")
    parser.add_argument("--master", default=DEFAULT_MASTER,
                         help=f"This project's master CSV to merge into (default: {DEFAULT_MASTER})")
    parser.add_argument("--out", default=None,
                         help="Where to write the merged result (default: overwrite --master)")
    parser.add_argument("--dry-run", action="store_true",
                         help="Print what would happen, don't write any file")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"[error] input file not found: {args.input}")
        return

    jobpulseke_df = load_jobpulseke(args.input)
    print(f"[ok] normalized {len(jobpulseke_df):,} jobpulseKe rows to this project's schema")
    print(jobpulseke_df["source"].value_counts().to_string())

    master_df = load_master(args.master)
    print(f"[ok] existing master: {len(master_df):,} rows")

    combined = pd.concat([master_df, jobpulseke_df], ignore_index=True)
    before = len(combined)
    combined = combined.drop_duplicates(subset=["job_id"], keep="first")
    after = len(combined)
    new_rows = after - len(master_df)

    print(
        f"\n=== Merge result: {after:,} total rows "
        f"({before - after:,} duplicates dropped, {new_rows:,} net new rows added) ==="
    )

    if args.dry_run:
        print("[dry-run] not writing any file")
        return

    out_path = args.out or args.master
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    combined.to_csv(out_path, index=False)
    print(f"Saved -> {out_path}")


if __name__ == "__main__":
    main()
