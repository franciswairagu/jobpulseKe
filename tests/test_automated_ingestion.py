import csv

import pytest

from scripts.publish_scraped_jobs import build_upload_rows


def _write_csv(path, fieldnames, rows):
    with path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def test_build_upload_rows_enriches_only_current_scrape(tmp_path):
    snapshot = tmp_path / "snapshot.csv"
    scraped = tmp_path / "scraped.csv"
    fields = ["job_id", "source", "source_job_id", "job_title", "job_description", "extracted_skills"]
    _write_csv(
        snapshot,
        fields,
        [
            {
                "job_id": "stable-id",
                "source": "myjobmag",
                "source_job_id": "mjm-1",
                "job_title": "Backend Engineer",
                "job_description": "Detailed description",
                "extracted_skills": '["python"]',
            },
            {
                "job_id": "other-id",
                "source": "fuzu",
                "source_job_id": "fuzu-2",
                "job_title": "Data Analyst",
                "job_description": "Not part of this scrape",
                "extracted_skills": "[]",
            },
        ],
    )
    _write_csv(
        scraped,
        ["job_id", "source", "source_job_id", "job_title", "job_description"],
        [
            {
                "job_id": "new-hash",
                "source": "myjobmag",
                "source_job_id": "mjm-1",
                "job_title": "Backend Engineer II",
                "job_description": "Short",
            },
            {
                "job_id": "new-id",
                "source": "remoteok",
                "source_job_id": "remote-3",
                "job_title": "Platform Engineer",
                "job_description": "Cloud infrastructure",
            },
        ],
    )

    fieldnames, rows, updated = build_upload_rows(snapshot, scraped)

    assert len(rows) == 2
    assert updated == 1
    existing = next(row for row in rows if row["source_job_id"] == "mjm-1")
    new = next(row for row in rows if row["source_job_id"] == "remote-3")
    assert existing["job_id"] == "stable-id"
    assert existing["job_title"] == "Backend Engineer II"
    assert existing["job_description"] == "Detailed description"
    assert existing["extracted_skills"] == '["python"]'
    assert new["extracted_skills"] == "[]"
    assert new["job_id"] == "new-id"
    assert fieldnames == fields


def test_build_upload_rows_rejects_empty_scrape(tmp_path):
    snapshot = tmp_path / "snapshot.csv"
    scraped = tmp_path / "scraped.csv"
    fields = ["job_id", "source", "source_job_id"]
    _write_csv(snapshot, fields, [{"job_id": "1", "source": "myjobmag", "source_job_id": "mjm-1"}])
    _write_csv(scraped, fields, [])

    with pytest.raises(ValueError, match="refusing to publish an empty batch"):
        build_upload_rows(snapshot, scraped)
