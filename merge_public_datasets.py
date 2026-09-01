"""
merge_public_datasets.py — supplement your live-scraped data with two
real, free, publicly available job-posting datasets from Hugging Face,
to responsibly close the gap toward a large target record count.

WHY THIS EXISTS: live scraping of national/regional African job boards
realistically tops out somewhere in the low tens of thousands of
*currently active* postings — see the README's "About the 100,000-record
target" section for the full explanation. These two datasets are the
most credible free supplement I could verify actually exist and are
downloadable without a paid API key:

  1. fantastic-jobs/7-million-jobs (huggingface.co/datasets/fantastic-jobs/7-million-jobs)
     ~6.99M global job postings, free, no license restriction found
     blocking academic/personal use.
  2. umaradnaan/IT_JOBS (huggingface.co/datasets/umaradnaan/IT_JOBS)
     IT-specific postings, Apache-2.0 licensed, 10M-100M rows.

IMPORTANT — READ BEFORE RUNNING: I verified these datasets exist and
are the right rough size via web search, but I have NOT been able to
inspect their exact column names directly (no network access to
huggingface.co from my environment). This script therefore:
  1. Loads each dataset and PRINTS its actual columns first.
  2. Uses keyword-based fuzzy column matching (e.g. any column with
     'title' in its name -> job_title) rather than hardcoded exact
     names, so it adapts to whatever the real schema turns out to be.
  3. Prints a sample of 3 rows before doing any filtering, so you can
     eyeball whether the auto-mapping looks right BEFORE it processes
     millions of rows.

If the auto-mapping guesses wrong for a field, the printed columns will
make it obvious what to fix in COLUMN_KEYWORD_MAP below — this is
meant to get you 90% of the way, with a quick manual check, not to be
a black box.

Usage:
    pip install datasets --break-system-packages
    python merge_public_datasets.py --inspect-only      # just print columns + sample, don't process
    python merge_public_datasets.py                     # filter to Africa, tag tech, save + merge
"""
import argparse
import os
import re
from collections import Counter

import pandas as pd

from config import (
    SCHEMA_COLUMNS, AFRICAN_COUNTRIES, AFRICAN_COUNTRY_CODES,
    AFRICAN_COUNTRY_CODES_ALPHA3, OUTPUT_DIR,
)
from utils.helpers import build_record, is_tech_job

try:
    from datasets import load_dataset
    HAS_DATASETS = True
except ImportError:
    HAS_DATASETS = False

HF_DATASETS = {
    # (hf_path, apply_tech_keyword_filter)
    # fantastic_jobs_hf is a GENERAL global jobs dataset -> needs the
    # tech-keyword filter to isolate tech roles.
    "fantastic_jobs_hf": ("fantastic-jobs/7-million-jobs", True),
    # it_jobs_hf REMOVED: inspected via --inspect-only and it turned out
    # to only have 3 columns (Domain, Job Title, "Projected Growth by
    # 2030") — a job-growth-projection reference table, not actual job
    # postings. No company/location/date/description fields exist at
    # all, so it's structurally incapable of contributing to this
    # dataset regardless of any matching logic. Leaving this note here
    # instead of silently deleting it so it's clear WHY it's gone if
    # you're comparing against an earlier run.
}

# Keyword -> schema field. First column whose name contains the keyword
# (case-insensitive) is used. Order matters (more specific keywords first).
COLUMN_KEYWORD_MAP = [
    ("job_title", ["job_title", "title", "position", "role"]),
    ("company", ["company", "employer", "organization"]),
    ("job_description", ["description", "desc", "summary", "detail"]),
    ("location", ["location", "city", "place"]),
    ("country", ["country", "nation"]),
    ("employment_type", ["employment_type", "job_type", "contract_type", "type"]),
    ("salary", ["salary", "pay", "compensation", "wage"]),
    ("currency", ["currency", "salary_currency"]),
    ("date_posted", ["date_posted", "posted", "date", "created"]),
    ("vacancy_url", ["url", "link", "apply"]),
    ("industry", ["industry", "sector"]),
    ("work_mode", ["remote", "work_mode", "workplace"]),
]


def guess_column_mapping(columns):
    """Best-effort keyword match of dataset columns to our schema fields."""
    mapping = {}
    lower_cols = {c: c.lower() for c in columns}
    for field, keywords in COLUMN_KEYWORD_MAP:
        for col, col_lower in lower_cols.items():
            if any(kw in col_lower for kw in keywords):
                mapping[field] = col
                break
    return mapping


def row_mentions_africa(row_text):
    """Fallback ONLY: substring search using full country NAMES (never
    codes, to avoid false positives like MA=Massachusetts)."""
    haystack = row_text.lower()
    return any(country.lower() in haystack for country in AFRICAN_COUNTRIES)


def match_country_value(value):
    """Exact-match a single structured country-field value against
    African full names, ISO alpha-2, and ISO alpha-3 codes. Returns the
    canonical country name if matched, else None. This is the reliable
    path — use it whenever a 'country' column was actually identified,
    instead of the free-text fallback."""
    if value is None:
        return None
    v = str(value).strip()
    if not v:
        return None
    v_upper = v.upper()
    if v_upper in AFRICAN_COUNTRY_CODES:
        return AFRICAN_COUNTRY_CODES[v_upper]
    if v_upper in AFRICAN_COUNTRY_CODES_ALPHA3:
        return AFRICAN_COUNTRY_CODES_ALPHA3[v_upper]
    v_title = v.title()
    for name in AFRICAN_COUNTRIES + list(AFRICAN_COUNTRY_CODES.values()):
        if v_title == name or v_title.replace("’", "'") == name:
            return name
    return None


def is_african_row(row, mapping):
    """
    Preferred path: if a 'country' column was identified, exact-match
    its value against names/ISO2/ISO3 codes (reliable, no false
    positives). Falls back to full-text name search ONLY if no country
    column was found at all — this fallback is what the original
    version always used, which is why a coded dataset silently returned
    zero matches despite genuinely containing African rows.
    """
    country_col = mapping.get("country")
    if country_col and country_col in row:
        matched = match_country_value(row.get(country_col))
        if matched:
            return matched
        # Country column exists but didn't match — trust it (don't also
        # fall back to text search here, or you re-introduce false
        # positives from unrelated text mentioning e.g. "Mali" as a name)
        return None

    # No country column identified at all — fall back to free-text search
    row_text = " ".join(str(v) for v in row.values() if v)
    if row_mentions_africa(row_text):
        for name in AFRICAN_COUNTRIES:
            if name.lower() in row_text.lower():
                return name
    return None


def diagnose_country_column(hf_path, mapping, sample_size=3000):
    """
    Quick, cheap sanity check run automatically during --inspect-only:
    stream `sample_size` rows, tally what's actually in the identified
    country column (or, if none identified, print a few raw location
    values instead), so you know BEFORE a multi-million-row full scan
    whether the field is coded, full-name, missing, or something else
    entirely (this is what a 13.6M-row / 0-kept run should have told us
    up front instead of after ~10 minutes of scanning).
    """
    print(f"\n--- Diagnostic: sampling {sample_size} rows to check country field ---")
    try:
        ds = load_dataset(hf_path, split="train", streaming=True)
    except Exception as e:
        print(f"[diagnostic error] {e}")
        return

    country_col = mapping.get("country")
    location_col = mapping.get("location")
    counter = Counter()
    checked = 0

    for row in ds:
        checked += 1
        val = row.get(country_col) if country_col else row.get(location_col)
        counter[str(val)] += 1
        if checked >= sample_size:
            break

    field_used = country_col or location_col or "(no country/location column identified!)"
    print(f"Sampled field: '{field_used}'")
    print(f"Top 15 values in this sample:")
    for val, count in counter.most_common(15):
        looks_african = match_country_value(val) is not None
        flag = "  <- African match" if looks_african else ""
        print(f"  {count:5d}x  {val!r}{flag}")

    if country_col and not any(match_country_value(v) for v in counter):
        print(
            "  [!] None of the top values matched a known African name/ISO "
            "code. Either this dataset genuinely has very little African "
            "coverage in this sample, or the values are in a format not "
            "yet handled (e.g. full country names with different spelling, "
            "or a numeric country ID needing a separate lookup table). "
            "Share this printout and I can adjust the matching."
        )


def process_hf_dataset(source_tag, hf_path, apply_tech_filter=True, inspect_only=False, sample_only=False):
    print(f"\n=== Loading {hf_path} (source tag: {source_tag}) ===")
    try:
        ds = load_dataset(hf_path, split="train", streaming=True)
    except Exception as e:
        print(f"[error] Could not load {hf_path}: {e}")
        print("        (check dataset name/split on huggingface.co — it may")
        print("         use a different split name, or require `pip install datasets`)")
        return None

    # Peek at first few rows to discover columns + preview data
    preview_rows = []
    for i, row in enumerate(ds):
        preview_rows.append(row)
        if i >= 2:
            break

    if not preview_rows:
        print(f"[error] {hf_path}: no rows returned")
        return None

    columns = list(preview_rows[0].keys())
    print(f"Columns found: {columns}")
    print(f"Sample row: {preview_rows[0]}")

    mapping = guess_column_mapping(columns)
    print(f"Auto-mapped fields: {mapping}")
    missing = [f for f, _ in COLUMN_KEYWORD_MAP if f not in mapping]
    if missing:
        print(f"[warning] Could not confidently map: {missing} — these will be left blank")

    if inspect_only:
        diagnose_country_column(hf_path, mapping)
        print("(--inspect-only: stopping here, nothing saved)")
        return None

    # Re-open non-streaming iteration for full pass (streaming mode used
    # above just to peek without downloading everything into memory twice)
    ds = load_dataset(hf_path, split="train", streaming=True)

    records = []
    scanned = 0
    kept = 0
    limit = 5000 if sample_only else None  # sample_only caps output for a quick trial run

    for row in ds:
        scanned += 1
        if scanned % 200000 == 0:
            print(f"  ...scanned {scanned:,} rows, kept {kept:,} so far")

        row_text = " ".join(str(v) for v in row.values() if v)
        matched_country = is_african_row(row, mapping)
        if not matched_country:
            continue

        title = row.get(mapping.get("job_title"), None)
        description = row.get(mapping.get("job_description"), None)
        if apply_tech_filter and not is_tech_job([str(title) if title else "", str(description) if description else ""]):
            continue

        rec = build_record(
            source=source_tag,
            source_job_id=str(row.get("id", scanned)),
            job_title=str(title) if title else None,
            company=str(row.get(mapping.get("company"))) if mapping.get("company") else None,
            job_description=str(description) if description else None,
            location=str(row.get(mapping.get("location"))) if mapping.get("location") else None,
            country=matched_country,
            employment_type=str(row.get(mapping.get("employment_type"))) if mapping.get("employment_type") else None,
            salary=str(row.get(mapping.get("salary"))) if mapping.get("salary") else None,
            currency=str(row.get(mapping.get("currency"))) if mapping.get("currency") else None,
            date_posted=str(row.get(mapping.get("date_posted"))) if mapping.get("date_posted") else None,
            vacancy_url=str(row.get(mapping.get("vacancy_url"))) if mapping.get("vacancy_url") else None,
            industry=str(row.get(mapping.get("industry"))) if mapping.get("industry") else None,
        )
        records.append(rec)
        kept += 1

        if limit and kept >= limit:
            print(f"  (sample_only cap of {limit} reached)")
            break

    print(f"Scanned {scanned:,} total rows, kept {kept:,} Africa-relevant tech postings")

    if not records:
        return None

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    df = pd.DataFrame(records, columns=SCHEMA_COLUMNS)
    out_path = os.path.join(OUTPUT_DIR, f"{source_tag}.csv")
    df.to_csv(out_path, index=False)
    print(f"Saved -> {out_path}")
    return df


def main():
    parser = argparse.ArgumentParser(description="Supplement scraped data with public HF datasets")
    parser.add_argument("--inspect-only", action="store_true",
                         help="Just print columns/sample for each dataset, don't process or save")
    parser.add_argument("--sample-only", action="store_true",
                         help="Cap each dataset at 5,000 kept rows for a quick trial run before a full pass")
    parser.add_argument("--datasets", nargs="+", choices=list(HF_DATASETS.keys()), default=None,
                         help="Which pre-registered HF datasets to process (default: all registered)")
    parser.add_argument("--hf-path", default=None,
                         help=(
                             "Process an arbitrary Hugging Face dataset by repo ID "
                             "(e.g. 'lukebarousse/data_jobs') instead of/in addition to "
                             "the pre-registered ones. Always run with --inspect-only "
                             "first to check its actual columns — the it_jobs_hf "
                             "incident (a dataset that turned out to have no location "
                             "data at all) is exactly why: I can't verify a dataset's "
                             "real schema without querying it directly, so don't trust "
                             "a dataset's description/size alone, check the columns."
                         ))
    parser.add_argument("--hf-tech-filter", action="store_true", default=True,
                         help="Apply the generic tech-keyword filter to --hf-path (default: on)")
    parser.add_argument("--no-hf-tech-filter", dest="hf_tech_filter", action="store_false",
                         help="Skip the tech-keyword filter for --hf-path (use if the dataset is already tech-scoped)")
    parser.add_argument("--merge-into-master", action="store_true",
                         help="After processing, merge results into output/master_africa_tech_jobs.csv (dedup on job_id)")
    args = parser.parse_args()

    if not HAS_DATASETS:
        print("The `datasets` package isn't installed. Run:")
        print("    pip install datasets --break-system-packages")
        return

    targets = args.datasets or list(HF_DATASETS.keys())
    frames = []
    for tag in targets:
        hf_path, apply_tech_filter = HF_DATASETS[tag]
        df = process_hf_dataset(
            tag, hf_path,
            apply_tech_filter=apply_tech_filter,
            inspect_only=args.inspect_only,
            sample_only=args.sample_only,
        )
        if df is not None:
            frames.append(df)

    if args.hf_path:
        # Ad-hoc dataset not in the registry. Derive a source tag from
        # the repo ID (e.g. "lukebarousse/data_jobs" -> "data_jobs_hf").
        tag = re.sub(r"[^a-z0-9]+", "_", args.hf_path.split("/")[-1].lower()).strip("_") + "_hf"
        df = process_hf_dataset(
            tag, args.hf_path,
            apply_tech_filter=args.hf_tech_filter,
            inspect_only=args.inspect_only,
            sample_only=args.sample_only,
        )
        if df is not None:
            frames.append(df)

    if args.inspect_only or not frames:
        return

    if args.merge_into_master:
        master_path = os.path.join(OUTPUT_DIR, "master_africa_tech_jobs.csv")
        if os.path.exists(master_path):
            existing = pd.read_csv(master_path)
            frames = [existing] + frames
        combined = pd.concat(frames, ignore_index=True)
        before = len(combined)
        combined = combined.drop_duplicates(subset=["job_id"], keep="first")
        combined.to_csv(master_path, index=False)
        print(f"\n=== Merged into master: {len(combined):,} records ({before - len(combined)} duplicates dropped) ===")
        print(f"Saved -> {master_path}")


if __name__ == "__main__":
    main()
