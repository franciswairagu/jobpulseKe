import pandas as pd

from app.services.job_service import ingest_jobs_from_dataframe


def _job_row(**overrides):
    row = {
        "job_id": "1", "source": "myjobmag", "source_job_id": "mjm-1",
        "job_title": "Backend Engineer", "company": "Acme Kenya",
        "job_description": "Python, Django, PostgreSQL, AWS required. 3 years experience.",
        "location": "Nairobi", "country": "Kenya", "work_mode": "Hybrid",
        "remote_eligible": 0, "employment_type": "Full-time",
        "date_posted": "2026-08-20", "application_deadline": "2026-09-30",
        "vacancy_url": "https://example.com/job/1",
    }
    row.update(overrides)
    return row


def test_recommendations_endpoint_returns_expected_shape(client, auth_headers):
    headers = auth_headers()
    r = client.get("/api/recommendations", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert set(body.keys()) == {"interview_platforms", "courses", "learning_resources"}


def test_recommendations_require_auth(client):
    r = client.get("/api/recommendations")
    assert r.status_code == 401


def test_recommended_jobs_reflect_real_job_data(client, db_session, auth_headers):
    df = pd.DataFrame([_job_row()])
    ingest_jobs_from_dataframe(db_session, df)
    headers = auth_headers()

    r = client.get("/api/jobs/recommended", headers=headers)
    assert r.status_code == 200
    jobs = r.json()
    assert len(jobs) == 1
    assert jobs[0]["title"] == "Backend Engineer"
    # No CV uploaded yet, so candidate has no skills -> everything is missing
    assert set(jobs[0]["missing_skills"]) == {"python", "django", "postgresql", "aws"}
    assert jobs[0]["match_score"] == 0.0
