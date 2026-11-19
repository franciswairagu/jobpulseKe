import datetime

import pandas as pd

from app.api import jobs as jobs_api
from app.services.job_service import ingest_jobs_from_dataframe, market_insights, mark_stale_jobs_removed, search_jobs
from app.models.enums import JobStatus
from app.models.job import Job


def _sample_job_row(**overrides):
    row = {
        "job_id": "1", "source": "myjobmag", "source_job_id": "mjm-1",
        "job_title": "Backend Engineer", "company": "Acme Kenya",
        "job_description": "Python, Django, PostgreSQL, AWS. 3 years experience required.",
        "location": "Nairobi", "country": "Kenya", "work_mode": "Hybrid",
        "remote_eligible": 0, "employment_type": "Full-time",
        "date_posted": "2026-08-20", "application_deadline": "2026-09-30",
        "vacancy_url": "https://example.com/job/1",
    }
    row.update(overrides)
    return row


def test_ingest_creates_job_with_skills(db_session):
    df = pd.DataFrame([_sample_job_row()])
    result = ingest_jobs_from_dataframe(db_session, df)
    assert result["created"] == 1

    job = db_session.query(Job).filter(Job.source_job_id == "mjm-1").first()
    assert job is not None
    assert job.status == JobStatus.AVAILABLE
    skill_names = {link.skill.name for link in job.skill_links}
    assert "python" in skill_names


def test_ingest_is_idempotent_on_rerun(db_session):
    df = pd.DataFrame([_sample_job_row()])
    ingest_jobs_from_dataframe(db_session, df)
    result = ingest_jobs_from_dataframe(db_session, df)
    assert result["updated"] == 1
    assert db_session.query(Job).count() == 1


def test_ingest_preserves_snapshot_skills_and_remote_flag(db_session):
    df = pd.DataFrame([
        _sample_job_row(
            job_description="",
            work_mode="",
            remote_eligible=1,
            extracted_skills='["kubernetes", "xgboost"]',
        )
    ])

    ingest_jobs_from_dataframe(db_session, df)
    job = db_session.query(Job).first()

    assert job.remote is True
    assert {"kubernetes", "xgboost"} <= {link.skill.name for link in job.skill_links}


def test_ingest_parses_string_remote_flag_as_boolean(db_session):
    df = pd.DataFrame([_sample_job_row(work_mode="unknown", remote_eligible="0")])

    ingest_jobs_from_dataframe(db_session, df)

    assert db_session.query(Job).first().remote is False


def test_new_ingest_records_discovery_time_not_source_scrape_date(db_session):
    df = pd.DataFrame([
        _sample_job_row(scraped_at="2020-01-01T00:00:00+00:00")
    ])

    ingest_jobs_from_dataframe(db_session, df)
    job = db_session.query(Job).first()
    original_created_at = job.created_at

    comparable_created_at = original_created_at
    if comparable_created_at.tzinfo is None:
        comparable_created_at = comparable_created_at.replace(tzinfo=datetime.timezone.utc)
    assert comparable_created_at >= datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=5)

    ingest_jobs_from_dataframe(db_session, df)
    db_session.refresh(job)
    assert job.created_at == original_created_at

    insights = market_insights(db_session)
    assert insights["jobs_added_this_week"] == 1


def test_search_jobs_filters_by_country(db_session):
    df = pd.DataFrame([
        _sample_job_row(source_job_id="k1", country="Kenya"),
        _sample_job_row(source_job_id="n1", country="Nigeria", job_id="2"),
    ])
    ingest_jobs_from_dataframe(db_session, df)

    jobs, total = search_jobs(db_session, country="Kenya")
    assert total == 1
    assert jobs[0].country == "Kenya"


def test_mark_stale_jobs_removed_updates_status(db_session):
    import datetime

    df = pd.DataFrame([_sample_job_row()])
    ingest_jobs_from_dataframe(db_session, df)
    job = db_session.query(Job).first()
    job.updated_at = datetime.datetime(2020, 1, 1, tzinfo=datetime.timezone.utc)
    db_session.add(job)
    db_session.commit()

    count = mark_stale_jobs_removed(db_session, cutoff_days=30)
    assert count == 1
    db_session.refresh(job)
    assert job.status == JobStatus.REMOVED


def test_jobs_api_lists_available_jobs(client, db_session):
    df = pd.DataFrame([_sample_job_row()])
    ingest_jobs_from_dataframe(db_session, df)

    r = client.get("/api/jobs")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 1
    assert body["jobs"][0]["title"] == "Backend Engineer"


def test_automated_ingest_requires_configured_token(client, monkeypatch):
    monkeypatch.setattr(jobs_api.settings, "AUTOMATED_INGEST_TOKEN", "test-token")

    response = client.post(
        "/api/jobs/ingest/automated",
        files={"file": ("jobs.csv", b"source,source_job_id\nmyjobmag,mjm-1\n", "text/csv")},
    )

    assert response.status_code == 401


def test_automated_ingest_rejects_missing_token_configuration(client, monkeypatch):
    monkeypatch.setattr(jobs_api.settings, "AUTOMATED_INGEST_TOKEN", "")

    response = client.post(
        "/api/jobs/ingest/automated",
        headers={"X-Ingestion-Token": "test-token"},
        files={"file": ("jobs.csv", b"source,source_job_id\nmyjobmag,mjm-1\n", "text/csv")},
    )

    assert response.status_code == 503


def test_automated_ingest_accepts_valid_token_and_csv(client, db_session, monkeypatch):
    monkeypatch.setattr(jobs_api.settings, "AUTOMATED_INGEST_TOKEN", "test-token")

    response = client.post(
        "/api/jobs/ingest/automated",
        headers={"X-Ingestion-Token": "test-token"},
        files={
            "file": (
                "jobs.csv",
                b"job_id,source,source_job_id,job_title,country\n1,myjobmag,0001,Backend Engineer,Kenya\n",
                "text/csv",
            )
        },
    )

    assert response.status_code == 200
    assert response.json()["created"] == 1
    assert db_session.query(Job).first().source_job_id == "0001"


def test_automated_ingest_preserves_existing_fields_when_scrape_is_sparse(
    client, db_session, monkeypatch
):
    monkeypatch.setattr(jobs_api.settings, "AUTOMATED_INGEST_TOKEN", "test-token")
    row = _sample_job_row(
        job_description="A detailed listing with Python and PostgreSQL requirements.",
        company="Acme Kenya",
        work_mode="Remote",
        remote_scope="Global",
        remote_eligible=1,
    )
    ingest_jobs_from_dataframe(db_session, pd.DataFrame([row]))
    job = db_session.query(Job).filter(Job.source_job_id == "mjm-1").first()

    sparse_row = pd.DataFrame(
        [
            {
                "source": "myjobmag",
                "source_job_id": "mjm-1",
                "job_title": "Backend Engineer",
                "job_description": "",
                "company": "",
                "country": "",
                "location": "",
                "work_mode": "unknown",
                "remote_scope": "",
                "employment_type": "",
                "vacancy_url": "",
                "date_posted": "",
                "application_deadline": "",
            }
        ]
    )
    response = client.post(
        "/api/jobs/ingest/automated",
        headers={"X-Ingestion-Token": "test-token"},
        files={"file": ("jobs.csv", sparse_row.to_csv(index=False).encode(), "text/csv")},
    )

    assert response.status_code == 200
    db_session.refresh(job)
    assert job.company == "Acme Kenya"
    assert job.description == "A detailed listing with Python and PostgreSQL requirements."
    assert job.country == "Kenya"
    assert job.city == "Nairobi"
    assert job.remote is True
    assert job.source_url == "https://example.com/job/1"


def test_job_status_update_requires_auth(client, db_session):
    df = pd.DataFrame([_sample_job_row()])
    ingest_jobs_from_dataframe(db_session, df)
    job = db_session.query(Job).first()

    r = client.patch(f"/api/jobs/{job.id}/status", json={"status": "FILLED"})
    assert r.status_code == 401


def test_job_status_update_records_history(client, db_session, auth_headers):
    df = pd.DataFrame([_sample_job_row()])
    ingest_jobs_from_dataframe(db_session, df)
    job = db_session.query(Job).first()
    headers = auth_headers()

    r = client.patch(f"/api/jobs/{job.id}/status", json={"status": "FILLED", "source": "manual_review"}, headers=headers)
    assert r.status_code == 200
    assert r.json()["status"] == "FILLED"

    r2 = client.get(f"/api/jobs/{job.id}/history")
    statuses = [h["status"] for h in r2.json()]
    assert "FILLED" in statuses
