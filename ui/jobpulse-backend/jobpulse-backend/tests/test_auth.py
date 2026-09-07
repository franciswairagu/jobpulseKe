def test_register_creates_user(client):
    r = client.post("/api/auth/register", json={"email": "alice@example.com", "password": "supersecret1"})
    assert r.status_code == 201
    body = r.json()
    assert body["email"] == "alice@example.com"
    assert body["is_active"] is True


def test_register_duplicate_email_rejected(client):
    client.post("/api/auth/register", json={"email": "bob@example.com", "password": "supersecret1"})
    r = client.post("/api/auth/register", json={"email": "bob@example.com", "password": "anotherpass1"})
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "EMAIL_ALREADY_REGISTERED"


def test_login_success_returns_tokens(client):
    client.post("/api/auth/register", json={"email": "carol@example.com", "password": "supersecret1"})
    r = client.post("/api/auth/login", data={"username": "carol@example.com", "password": "supersecret1"})
    assert r.status_code == 200
    body = r.json()
    assert "access_token" in body and "refresh_token" in body


def test_login_wrong_password_rejected(client):
    client.post("/api/auth/register", json={"email": "dave@example.com", "password": "supersecret1"})
    r = client.post("/api/auth/login", data={"username": "dave@example.com", "password": "wrongpassword"})
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "INVALID_CREDENTIALS"


def test_me_requires_auth(client):
    r = client.get("/api/auth/me")
    assert r.status_code == 401


def test_me_returns_current_user(client, auth_headers):
    headers = auth_headers("erin@example.com")
    r = client.get("/api/auth/me", headers=headers)
    assert r.status_code == 200
    assert r.json()["email"] == "erin@example.com"


def test_refresh_token_issues_new_access_token(client):
    client.post("/api/auth/register", json={"email": "frank@example.com", "password": "supersecret1"})
    r = client.post("/api/auth/login", data={"username": "frank@example.com", "password": "supersecret1"})
    refresh_token = r.json()["refresh_token"]
    r2 = client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert r2.status_code == 200
    assert "access_token" in r2.json()
