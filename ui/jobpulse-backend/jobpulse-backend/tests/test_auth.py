import builtins

import app.api.auth as auth_api
import pytest

from app.core.google_auth import GoogleAuthUnavailable, verify_google_id_token
from app.core.config import get_settings
from app.core.security import create_refresh_token


def test_password_auth_endpoints_are_disabled(client):
    register = client.post(
        "/api/auth/register",
        json={"email": "fake@example.com", "password": "password123"},
    )
    login = client.post(
        "/api/auth/login",
        json={"email": "fake@example.com", "password": "password123"},
    )

    assert register.status_code == 410
    assert login.status_code == 410


def test_google_login_creates_verified_account(client, monkeypatch):
    monkeypatch.setattr(get_settings(), "GOOGLE_CLIENT_ID", "test-client-id")
    monkeypatch.setattr(
        auth_api,
        "verify_google_id_token",
        lambda token, audience: {
            "sub": "google-user-123",
            "email": "New.User@gmail.com",
            "email_verified": True,
            "name": "New User",
        },
    )

    response = client.post("/api/auth/google", json={"credential": "verified-id-token"})

    assert response.status_code == 200
    assert response.json()["access_token"]
    profile = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {response.json()['access_token']}"},
    )
    assert profile.status_code == 200
    assert profile.json()["email"] == "new.user@gmail.com"
    assert profile.json()["name"] == "New User"


def test_google_login_rejects_unverified_email(client, monkeypatch):
    monkeypatch.setattr(get_settings(), "GOOGLE_CLIENT_ID", "test-client-id")
    monkeypatch.setattr(
        auth_api,
        "verify_google_id_token",
        lambda token, audience: {
            "sub": "google-user-123",
            "email": "fake@example.com",
            "email_verified": False,
        },
    )

    response = client.post("/api/auth/google", json={"credential": "unverified-id-token"})

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNVERIFIED_GOOGLE_ACCOUNT"


def test_google_login_reports_missing_verifier_dependency(client, monkeypatch):
    monkeypatch.setattr(get_settings(), "GOOGLE_CLIENT_ID", "test-client-id")

    def missing_dependency(token, audience):
        raise GoogleAuthUnavailable("Install the backend requirements to enable Google sign-in.")

    monkeypatch.setattr(auth_api, "verify_google_id_token", missing_dependency)

    response = client.post("/api/auth/google", json={"credential": "some-token"})

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "GOOGLE_SIGN_IN_UNAVAILABLE"


def test_google_verifier_import_is_lazy_and_has_clear_missing_dependency_error(monkeypatch):
    original_import = builtins.__import__

    def deny_google_auth(name, *args, **kwargs):
        if name.startswith("google.auth") or name == "google.oauth2":
            raise ImportError("google-auth is not installed")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", deny_google_auth)

    with pytest.raises(GoogleAuthUnavailable, match="Install the backend requirements"):
        verify_google_id_token("id-token", "client-id")


def test_refresh_token_requires_an_active_account(client, auth_headers):
    headers = auth_headers("refresh@example.com")
    user_id = client.get("/api/auth/me", headers=headers).json()["id"]

    response = client.post(
        "/api/auth/refresh",
        json={"refresh_token": create_refresh_token(user_id, {"auth_provider": "google"})},
    )

    assert response.status_code == 200
    assert response.json()["access_token"]


def test_legacy_password_tokens_are_rejected(client, auth_headers):
    headers = auth_headers("legacy@example.com")
    user_id = client.get("/api/auth/me", headers=headers).json()["id"]
    legacy_token = auth_api.create_access_token(user_id)

    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {legacy_token}"},
    )

    assert response.status_code == 401
