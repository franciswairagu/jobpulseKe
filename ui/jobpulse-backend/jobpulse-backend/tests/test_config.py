from app.core.config import _load_environment_files


def test_environment_loader_skips_blank_backend_value_and_uses_repository_value(tmp_path):
    repo = tmp_path / "repo"
    backend = repo / "ui" / "backend"
    (repo / ".git").mkdir(parents=True)
    backend.mkdir(parents=True)
    (backend / ".env").write_text("GOOGLE_CLIENT_ID=\nBACKEND_VALUE=backend\n")
    (repo / ".env").write_text("GOOGLE_CLIENT_ID=google-client-id\nBACKEND_VALUE=repo\n")
    environ = {}

    _load_environment_files(backend, environ)

    assert environ["GOOGLE_CLIENT_ID"] == "google-client-id"
    assert environ["BACKEND_VALUE"] == "backend"


def test_environment_loader_keeps_existing_process_values(tmp_path):
    repo = tmp_path / "repo"
    backend = repo / "backend"
    (repo / ".git").mkdir(parents=True)
    backend.mkdir()
    (repo / ".env").write_text("GOOGLE_CLIENT_ID=file-client-id\n")
    environ = {"GOOGLE_CLIENT_ID": "process-client-id"}

    _load_environment_files(backend, environ)

    assert environ["GOOGLE_CLIENT_ID"] == "process-client-id"
