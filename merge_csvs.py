"""
merge_csvs.py — merge any number of already-saved, schema-conformant
CSVs (e.g. output/master_africa_tech_jobs.csv + output/fantastic_jobs_hf.csv,
or any future output/<source>.csv) into one deduplicated master file,
without re-running any scraper or dataset scan.

Usage:
    # Merge two specific files, write back to master:
    python merge_csvs.py output/master_africa_tech_jobs.csv output/fantastic_jobs_hf.csv

    # Merge EVERY csv currently in output/ (handy after a full run):
    python merge_csvs.py --all

    # Write somewhere other than the default master path:
    python merge_csvs.py output/a.csv output/b.csv --out output/combined.csv

Dedup is on `job_id` (same key every scraper/dataset script already
produces), so re-merging the same file twice is always safe — it just
won't add duplicates.
"""
import argparse
import glob
import os

import pandas as pd

from config import SCHEMA_COLUMNS, OUTPUT_DIR

DEFAULT_MASTER = os.path.join(OUTPUT_DIR, "master_africa_tech_jobs.csv")


def load_and_align(path):
    df = pd.read_csv(path)
    missing = [c for c in SCHEMA_COLUMNS if c not in df.columns]
    if missing:
        print(f"[warning] {path} is missing columns {missing} — filling with blank")
        for c in missing:
            df[c] = None
    extra = [c for c in df.columns if c not in SCHEMA_COLUMNS]
    if extra:
        print(f"[warning] {path} has unexpected columns {extra} — dropping them")
    return df[SCHEMA_COLUMNS]


def main():
    parser = argparse.ArgumentParser(description="Merge schema-conformant job CSVs, dedup on job_id")
    parser.add_argument("files", nargs="*", help="CSV files to merge")
    parser.add_argument("--all", action="store_true", help=f"Merge every *.csv currently in {OUTPUT_DIR}/")
    parser.add_argument("--out", default=DEFAULT_MASTER, help=f"Output path (default: {DEFAULT_MASTER})")
    args = parser.parse_args()

    if args.all:
        files = sorted(glob.glob(os.path.join(OUTPUT_DIR, "*.csv")))
        # Avoid merging the master into itself as a "new" input when
        # writing back to the same path
        files = [f for f in files if os.path.abspath(f) != os.path.abspath(args.out)]
    else:
        files = args.files

    if not files:
        print("No input files given. Use positional file paths or --all.")
        return

    frames = []
    for f in files:
        if not os.path.exists(f):
            print(f"[skip] {f} not found")
            continue
        df = load_and_align(f)
        print(f"[ok] {f}: {len(df):,} rows")
        frames.append(df)

    if not frames:
        print("Nothing to merge.")
        return

    combined = pd.concat(frames, ignore_index=True)
    before = len(combined)
    combined = combined.drop_duplicates(subset=["job_id"], keep="first")
    after = len(combined)

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    combined.to_csv(args.out, index=False)
    print(f"\n=== Merged {len(files)} file(s): {after:,} unique records "
          f"({before - after:,} duplicates dropped) ===")
    print(f"Saved -> {args.out}")


if __name__ == "__main__":
    main()
