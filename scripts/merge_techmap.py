"""
merge_techmap.py — ingest TechMap Kenya job data (JSONL / gzipped JSONL)
into the project's canonical 22-column schema and save as a merge-ready CSV.

TechMap records are richly structured JSON with nested fields under
json.schemaOrg (Schema.org JobPosting), json.inferredTags, company, location,
and salary.  This script extracts and flattens them into the flat schema
every scraper already produces, using the same build_record() helper so
job_id hashing, work_mode guessing, and tech_category classification are
all consistent with the rest of the pipeline.

Usage:
    # Default: read data/techmap/*.jsonl*, write data/raw/techmap_jobs.csv
    python scripts/merge_techmap.py

    # Dry run (print stats, don't write):
    python scripts/merge_techmap.py --dry-run

    # Merge straight into the Africa master CSV:
    python scripts/merge_techmap.py --merge-into-master

    # Point at a different techmap directory:
    python scripts/merge_techmap.py --input data/techmap
"""
import argparse
import gzip
import json
import os
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.scraping_config import SCHEMA_COLUMNS, OUTPUT_DIR
from src.utils.helpers import build_record, clean_text

DEFAULT_INPUT = os.path.join("data", "techmap")
DEFAULT_OUT = os.path.join("data", "raw", "techmap_jobs.csv")


# ── helpers ──────────────────────────────────────────────────────────────

def _open(path):
    """Return an opener that handles both .jsonl and .jsonl.gz."""
    if path.endswith(".gz"):
        return gzip.open(path, "rt", encoding="utf-8")
    return open(path, "r", encoding="utf-8")


def _safe_str(val):
    """NaN/None-safe conversion to cleaned string."""
    if val is None:
        return None
    if isinstance(val, float) and pd.isna(val):
        return None
    s = str(val).strip()
    return s if s else None


def _schema_org(rec):
    """Shorthand for the nested json.schemaOrg dict (may be absent)."""
    return rec.get("json", {}).get("schemaOrg", {}) or {}


def _inferred_tags(rec):
    return rec.get("json", {}).get("inferredTags", {}) or {}


def _location_parts(rec):
    """Build a location string from structured fields, falling back to
    the top-level location dict or plain text."""
    so = _schema_org(rec)
    loc = so.get("jobLocation", {})
    addr = loc.get("address", {}) if loc else {}

    parts = []
    if addr.get("addressLocality"):
        parts.append(addr["addressLocality"])
    if addr.get("addressRegion"):
        parts.append(addr["addressRegion"])
    if addr.get("addressCountry"):
        parts.append(addr["addressCountry"])

    if parts:
        return ", ".join(parts)

    # fallback: top-level location object
    top_loc = rec.get("location", {})
    if isinstance(top_loc, dict):
        name = top_loc.get("name")
        if name:
            return name
    return None


def _country(rec):
    """Extract ISO country code or full name from Schema.org address."""
    so = _schema_org(rec)
    addr = so.get("jobLocation", {}).get("address", {}) if so.get("jobLocation") else {}
    code = addr.get("addressCountry")
    if code:
        # Schema.org sometimes gives full name, sometimes ISO code
        if len(code) == 2:
            from src.scraping_config import AFRICAN_COUNTRY_CODES
            return AFRICAN_COUNTRY_CODES.get(code.upper(), code)
        return code
    # fallback: top-level location
    top_loc = rec.get("location", {})
    if isinstance(top_loc, dict):
        cc = top_loc.get("countryCode") or top_loc.get("country")
        if cc:
            if len(cc) == 2:
                from src.scraping_config import AFRICAN_COUNTRY_CODES
                return AFRICAN_COUNTRY_CODES.get(cc.upper(), cc)
            return cc
    return None


def _work_mode(rec):
    """Derive work_mode from inferred tags or text."""
    tags = _inferred_tags(rec)
    work_types = [w.lower() for w in (tags.get("WORK_TYPES") or [])]
    if "remote" in work_types:
        return "remote"
    if "hybrid" in work_types:
        return "hybrid"
    if any(w in ("fulltime", "parttime", "contract", "flextime", "shift")
           for w in work_types):
        return "onsite"
    # fall back to text-based guess (handled by build_record)
    return None


def _employment_type(rec):
    so = _schema_org(rec)
    et = _safe_str(so.get("employmentType"))
    if et:
        return et
    tags = _inferred_tags(rec)
    work_types = tags.get("WORK_TYPES") or []
    return work_types[0] if work_types else None


def _salary_and_currency(rec):
    """Extract salary info.  TechMap mostly gives currency code, not amount."""
    so = _schema_org(rec)
    currency = _safe_str(so.get("salaryCurrency"))
    # TechMap doesn't store salary amounts at the top level; check company/salary dicts
    sal = rec.get("salary", {})
    amount = None
    if isinstance(sal, dict):
        amount = _safe_str(sal.get("amount")) or _safe_str(sal.get("text"))
    return amount, currency


def _source_tag(rec):
    """Convert TechMap source like 'personio_ke' -> 'techmap_personio'."""
    raw = rec.get("source") or rec.get("portal") or "unknown"
    # strip country suffix (_ke) and prefix with techmap_
    base = raw.split("_")[0] if "_" in raw else raw
    return f"techmap_{base}"


# ── core ─────────────────────────────────────────────────────────────────

def load_techmap_dir(input_dir):
    """Read all JSONL files from input_dir, return list of schema-conformant dicts."""
    files = sorted(Path(input_dir).glob("*.jsonl")) + sorted(Path(input_dir).glob("*.jsonl.gz"))
    if not files:
        print(f"[error] No .jsonl or .jsonl.gz files found in {input_dir}")
        return []

    records = []
    skipped = 0

    for fpath in files:
        count = 0
        with _open(str(fpath)) as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    skipped += 1
                    continue

                source = _source_tag(rec)
                source_job_id = _safe_str(rec.get("idInSource"))
                job_title = _safe_str(rec.get("name"))
                if not job_title:
                    skipped += 1
                    continue

                job_description = _safe_str(rec.get("text"))
                vacancy_url = _safe_str(rec.get("url"))

                # company: prefer schemaOrg, fallback to top-level company dict
                so = _schema_org(rec)
                org = so.get("hiringOrganization", {}) or {}
                company = _safe_str(org.get("name"))
                if not company:
                    top_co = rec.get("company", {})
                    if isinstance(top_co, dict):
                        company = _safe_str(top_co.get("name"))

                location = _location_parts(rec)
                country = _country(rec)
                work_mode = _work_mode(rec)
                employment_type = _employment_type(rec)
                salary, currency = _salary_and_currency(rec)

                date_posted = _safe_str(so.get("datePosted"))
                application_deadline = _safe_str(so.get("validThrough"))
                industry = _safe_str(so.get("industry"))
                education_required = _safe_str(so.get("educationRequirements"))
                experience_required = _safe_str(so.get("qualifications"))

                # job_field from relevantOccupation or inferred JOBNAMES
                job_field = _safe_str(so.get("relevantOccupation"))
                if not job_field:
                    jobnames = _inferred_tags(rec).get("JOBNAMES") or []
                    if jobnames:
                        job_field = jobnames[0]

                record = build_record(
                    source=source,
                    source_job_id=source_job_id,
                    job_title=job_title,
                    company=company,
                    job_description=job_description,
                    location=location,
                    country=country,
                    work_mode=work_mode,
                    employment_type=employment_type,
                    experience_required=experience_required,
                    education_required=education_required,
                    salary=salary,
                    currency=currency,
                    date_posted=date_posted,
                    application_deadline=application_deadline,
                    industry=industry,
                    job_field=job_field,
                    vacancy_url=vacancy_url,
                )
                records.append(record)
                count += 1

        print(f"[ok] {fpath.name}: {count:,} records loaded")

    if skipped:
        print(f"[info] {skipped} records skipped (missing title or parse error)")

    return records


def main():
    parser = argparse.ArgumentParser(description="Merge TechMap Kenya JSONL data into pipeline schema")
    parser.add_argument("--input", default=DEFAULT_INPUT, help=f"Directory with JSONL files (default: {DEFAULT_INPUT})")
    parser.add_argument("--out", default=DEFAULT_OUT, help=f"Output CSV path (default: {DEFAULT_OUT})")
    parser.add_argument("--dry-run", action="store_true", help="Print stats only, don't write file")
    parser.add_argument("--merge-into-master", action="store_true", help="Also merge into the Africa master CSV")
    args = parser.parse_args()

    if not os.path.isdir(args.input):
        print(f"[error] Input directory not found: {args.input}")
        return

    print("=" * 70)
    print("TECHMAP DATA INGESTION")
    print("=" * 70)

    records = load_techmap_dir(args.input)
    if not records:
        print("No records to process.")
        return

    df = pd.DataFrame(records, columns=SCHEMA_COLUMNS)
    before = len(df)
    df = df.drop_duplicates(subset=["job_id"], keep="first")
    after = len(df)
    if before != after:
        print(f"[info] {before - after} intra-source duplicates removed")

    print(f"\nTotal TechMap records: {after:,}")

    # Source breakdown
    print("\nBy source:")
    print(df["source"].value_counts().to_string())

    # Work mode breakdown
    print("\nBy work_mode:")
    print(df["work_mode"].value_counts().to_string())

    if args.dry_run:
        print("\n[dry-run] No file written.")
        return

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    df.to_csv(args.out, index=False)
    print(f"\nSaved -> {args.out}")

    if args.merge_into_master:
        master_path = os.path.join(OUTPUT_DIR, "master_africa_tech_jobs.csv")
        if os.path.exists(master_path):
            existing = pd.read_csv(master_path, low_memory=False)
            for col in SCHEMA_COLUMNS:
                if col not in existing.columns:
                    existing[col] = None
            existing = existing[SCHEMA_COLUMNS]
            combined = pd.concat([existing, df], ignore_index=True)
            before_m = len(combined)
            combined = combined.drop_duplicates(subset=["job_id"], keep="first")
            after_m = len(combined)
            combined.to_csv(master_path, index=False)
            print(f"\nMerged into master: {after_m:,} total ({before_m - after_m} duplicates dropped)")
            print(f"Saved -> {master_path}")
        else:
            os.makedirs(os.path.dirname(master_path), exist_ok=True)
            df.to_csv(master_path, index=False)
            print(f"\nCreated new master with {after:,} records -> {master_path}")

    print("=" * 70)


if __name__ == "__main__":
    main()
