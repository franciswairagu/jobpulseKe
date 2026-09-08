import pandas as pd

from app.services.job_service import ingest_jobs_from_dataframe, mark_stale_jobs_removed, search_jobs
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
