import os
import uuid

os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("LOCAL_STORAGE_DIR", "./test_uploads")
os.environ.setdefault("ENVIRONMENT", "development")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.security import create_access_token
from app.database import Base, get_db
from app.main import app
from app.models.user import Profile, User


@pytest.fixture(scope="function")
def db_engine(tmp_path):
    db_path = tmp_path / f"test_{uuid.uuid4().hex}.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(db_engine):
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(db_engine):
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(client, db_engine):
    def _make(email="user@example.com"):
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
        db = TestingSessionLocal()
        user = User(email=email.lower(), hashed_password="oauth-only")
        db.add(user)
        db.flush()
        db.add(Profile(user_id=user.id, name="Test User"))
        db.commit()
        token = create_access_token(str(user.id), {"auth_provider": "google"})
        db.close()
        return {"Authorization": f"Bearer {token}"}

    return _make
