#!/usr/bin/env python3
"""Publish only this run's scraped jobs to the authenticated backend endpoint."""

import argparse
import csv
import os
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlparse

import requests

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SNAPSHOT = PROJECT_ROOT / "data" / "processed" / "deployment_snapshot.csv"
DEFAULT_SCRAPED_DATA = PROJECT_ROOT / "output" / "master_africa_tech_jobs.csv"
UPLOAD_BATCH_SIZE = 500
REQUEST_TIMEOUT = (20, 600)


def _read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    try:
        csv.field_size_limit(sys.maxsize)
    except OverflowError:
        csv.field_size_limit(2**31 - 1)

    with path.open(newline="", encoding="utf-8-sig") as source:
        reader = csv.DictReader(source)
        if not reader.fieldnames:
            raise ValueError(f"{path} has no CSV header")
        return reader.fieldnames, [
            {key: value or "" for key, value in row.items() if key is not None}
            for row in reader
        ]


def _identity(row: dict[str, str], path: Path, row_number: int) -> tuple[str, str]:
    source = row.get("source", "").strip()
    source_job_id = row.get("source_job_id", "").strip()
    if not source or not source_job_id:
        raise ValueError(f"{path} row {row_number} is missing source or source_job_id")
    return source, source_job_id


def build_upload_rows(
    snapshot_path: Path = DEFAULT_SNAPSHOT,
    scraped_path: Path = DEFAULT_SCRAPED_DATA,
) -> tuple[list[str], list[dict[str, str]], int]:
    """Enrich this run's rows from the snapshot without uploading its full baseline."""
    snapshot_fields, snapshot_rows = _read_csv(snapshot_path)
    required_fields = {"job_id", "source", "source_job_id"}
    missing = required_fields - set(snapshot_fields)
    if missing:
        raise ValueError(f"{snapshot_path} is missing required columns: {', '.join(sorted(missing))}")

    known_rows = {}
    for row_number, row in enumerate(snapshot_rows, start=2):
        key = _identity(row, snapshot_path, row_number)
        if key in known_rows:
            raise ValueError(f"{snapshot_path} contains duplicate job identity {key!r}")
        known_rows[key] = row

    _, scraped_rows = _read_csv(scraped_path)
    if not scraped_rows:
        raise ValueError(f"{scraped_path} contains no scraped jobs; refusing to publish an empty batch")

    upload_rows: dict[tuple[str, str], dict[str, str]] = {}
    updated = 0
    for row_number, scraped_row in enumerate(scraped_rows, start=2):
        key = _identity(scraped_row, scraped_path, row_number)
        current = upload_rows.get(key)
        from_snapshot = current is None and key in known_rows
        if current is None:
            current = (
                dict(known_rows[key])
                if from_snapshot
                else {field: "" for field in snapshot_fields}
            )
            if not from_snapshot and "extracted_skills" in current:
                current["extracted_skills"] = "[]"
        for field in snapshot_fields:
            value = scraped_row.get(field, "").strip()
            if not value or (field == "job_id" and from_snapshot):
                continue
            if field == "job_description" and current.get(field):
                current[field] = max(current[field], value, key=len)
            else:
                current[field] = value
        current["source"], current["source_job_id"] = key
        upload_rows[key] = current
        if from_snapshot:
            updated += 1

    return snapshot_fields, list(upload_rows.values()), updated


def _endpoint(api_url: str) -> str:
    parsed = urlparse(api_url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError("JOBPULSE_API_URL must be an HTTPS backend base URL")
    return f"{api_url.rstrip('/')}/api/jobs/ingest/automated"


def publish_batches(api_url: str, token: str, fieldnames: list[str], rows: list[dict[str, str]]) -> tuple[int, int]:
    endpoint = _endpoint(api_url)
    created = updated = 0
    with tempfile.TemporaryDirectory(prefix="jobpulse-ingestion-") as temp_dir:
        for batch_number, start in enumerate(range(0, len(rows), UPLOAD_BATCH_SIZE), start=1):
            batch = rows[start : start + UPLOAD_BATCH_SIZE]
            batch_path = Path(temp_dir) / f"jobs-{batch_number}.csv"
            with batch_path.open("w", newline="", encoding="utf-8") as output:
                writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\n")
                writer.writeheader()
                writer.writerows(batch)

            with batch_path.open("rb") as upload:
                response = requests.post(
                    endpoint,
                    headers={"X-Ingestion-Token": token},
                    files={"file": (batch_path.name, upload, "text/csv")},
                    timeout=REQUEST_TIMEOUT,
                    allow_redirects=False,
                )
            if response.is_redirect:
                raise RuntimeError("Backend ingestion endpoint redirected; refusing to forward the token.")
            response.raise_for_status()
            result = response.json()
            if not isinstance(result, dict):
                raise RuntimeError("Backend returned an invalid ingestion response.")
            if result.get("skipped") != 0 or result.get("total_processed") != len(batch):
                raise RuntimeError(
                    f"Backend processed an unexpected batch result: "
                    f"expected {len(batch)}, received {result!r}"
                )
            created += result.get("created", 0)
            updated += result.get("updated", 0)
            print(f"Uploaded batch {batch_number}: {len(batch)} jobs")
    return created, updated


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish the current scraper output to JobPulse.")
    parser.add_argument("--snapshot", type=Path, default=DEFAULT_SNAPSHOT)
    parser.add_argument("--scraped-data", type=Path, default=DEFAULT_SCRAPED_DATA)
    args = parser.parse_args()

    api_url = os.getenv("JOBPULSE_API_URL", "").strip()
    token = os.getenv("JOBPULSE_INGEST_TOKEN", "")
    if not api_url or not token:
        parser.error("JOBPULSE_API_URL and JOBPULSE_INGEST_TOKEN must be configured")

    try:
        fieldnames, rows, existing_count = build_upload_rows(args.snapshot, args.scraped_data)
        print(
            f"Prepared {len(rows):,} scraped jobs "
            f"({existing_count:,} matching snapshot records, {len(rows) - existing_count:,} new)."
        )
        created, updated = publish_batches(api_url, token, fieldnames, rows)
    except (OSError, ValueError, requests.RequestException, RuntimeError) as exc:
        print(f"Automated ingestion failed: {exc}", file=sys.stderr)
        return 1

    print(f"Backend ingestion complete: {created:,} created, {updated:,} updated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
