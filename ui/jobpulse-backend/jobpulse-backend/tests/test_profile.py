from app.core.storage import LocalStorageBackend
import app.api.cv as cv_api


def test_profile_can_be_viewed_and_updated(client, auth_headers):
    headers = auth_headers()

    response = client.get("/api/profile", headers=headers)
    assert response.status_code == 200
    assert response.json()["email"] == "user@example.com"

    updated = client.patch(
        "/api/profile",
        headers=headers,
        json={
            "name": "Ada Lovelace",
            "country": "Kenya",
            "career_interest": "Data Engineering",
            "years_experience": 4,
        },
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "Ada Lovelace"
    assert updated.json()["country"] == "Kenya"
    assert updated.json()["years_experience"] == 4


def test_profile_rejects_invalid_experience(client, auth_headers):
    response = client.patch(
        "/api/profile",
        headers=auth_headers(),
        json={"years_experience": 71},
    )

    assert response.status_code == 422


def test_saved_cv_can_be_downloaded_only_by_its_owner(client, auth_headers, monkeypatch, tmp_path):
    storage = LocalStorageBackend(str(tmp_path / "cvs"))
    monkeypatch.setattr(cv_api, "get_storage_backend", lambda: storage)
    owner_headers = auth_headers("owner@example.com")
    content = b"%PDF-1.4 test document"

    upload = client.post(
        "/api/cv/upload",
        headers=owner_headers,
        files={"file": ("resume.pdf", content, "application/pdf")},
    )

    assert upload.status_code == 201
    resume_id = upload.json()["resume_id"]
    latest = client.get("/api/cv/latest", headers=owner_headers)
    assert latest.status_code == 200
    assert latest.json()["resume_id"] == resume_id
    assert latest.json()["original_filename"] == "resume.pdf"

    downloaded = client.get(f"/api/cv/{resume_id}/file", headers=owner_headers)
    assert downloaded.status_code == 200
    assert downloaded.content == content

    other_user = client.get(
        f"/api/cv/{resume_id}/file",
        headers=auth_headers("other@example.com"),
    )
    assert other_user.status_code == 403
