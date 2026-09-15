from datetime import timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import DateTime, create_engine
from sqlalchemy.dialects.sqlite.base import DATETIME as SQLiteDateTime
from sqlalchemy.dialects.sqlite.pysqlite import SQLiteDialect_pysqlite
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.core.supabase_storage as supabase_storage
import app.models  # noqa: F401
import app.services.notification_service as notification_service
from app.db.base import Base
from app.db.Session import get_db
from app.main import app


def add_utc_timezone(value):
    if value is not None and value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value


class DateTimeWithTimezone(SQLiteDateTime):
    def result_processor(self, dialect, coltype):
        original_processor = super().result_processor(dialect, coltype)

        def process(value):
            if original_processor is not None:
                value = original_processor(value)
            return add_utc_timezone(value)

        return process


SQLiteDialect_pysqlite.colspecs = {
    **SQLiteDialect_pysqlite.colspecs,
    DateTime: DateTimeWithTimezone,
}


@pytest.fixture()
def db_session(monkeypatch):
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    Base.metadata.create_all(engine)

    # Notification delivery opens its own session (it may run as a background task,
    # outliving the request's session) via app.db.Session.SessionLocal, which is bound
    # to the real DATABASE_URL. Point it at this test's in-memory engine instead, so
    # background delivery reads/writes the same data the test set up.
    monkeypatch.setattr(notification_service, "SessionLocal", TestingSessionLocal)

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture(autouse=True)
def mock_email_provider(monkeypatch):
    """Prevent every test from making a real Resend API call; records what was sent."""
    sent = []

    def fake_send_email(*, to, subject, body):
        sent.append({"to": to, "subject": subject, "body": body})

    monkeypatch.setattr(notification_service, "send_email", fake_send_email)
    return sent


@pytest.fixture(autouse=True)
def mock_storage(monkeypatch):
    """Prevent every test from making a real Supabase Storage call; a simple
    in-memory dict stands in for the bucket."""
    objects: dict[str, bytes] = {}

    def fake_upload_object(storage_key, content, content_type):
        objects[storage_key] = content

    def fake_delete_object(storage_key):
        objects.pop(storage_key, None)

    def fake_create_signed_url(storage_key, expires_in):
        if storage_key not in objects:
            raise supabase_storage.StorageError("object not found")
        return f"https://fake-storage.test/{storage_key}?expires_in={expires_in}"

    monkeypatch.setattr(supabase_storage, "upload_object", fake_upload_object)
    monkeypatch.setattr(supabase_storage, "delete_object", fake_delete_object)
    monkeypatch.setattr(supabase_storage, "create_signed_url", fake_create_signed_url)
    return objects


@pytest.fixture()
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def register_and_login(client, email: str, password: str, role: str) -> dict:
    client.post("/auth/register", json={"email": email, "password": password, "role": role})
    response = client.post("/auth/login", json={"email": email, "password": password})
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def client_auth_headers(client):
    return register_and_login(client, "client@example.com", "Password123!", "CLIENT")


@pytest.fixture()
def freelancer_auth_headers(client):
    return register_and_login(client, "freelancer@example.com", "Password123!", "FREELANCER")


@pytest.fixture()
def active_contract(client, client_auth_headers, freelancer_auth_headers):
    job = client.post(
        "/jobs",
        json={"title": "Build a website", "description": "Simple landing page", "budget": "500.00"},
        headers=client_auth_headers,
    ).json()
    client.patch(f"/jobs/{job['id']}", json={"status": "PUBLISHED"}, headers=client_auth_headers)

    proposal = client.post(
        f"/jobs/{job['id']}/proposals",
        json={"cover_letter": "I can do this", "bid_amount": "500.00", "estimated_duration": "2 weeks"},
        headers=freelancer_auth_headers,
    ).json()
    client.patch(f"/proposals/{proposal['id']}", json={"status": "ACCEPTED"}, headers=client_auth_headers)

    contracts = client.get("/contracts", headers=client_auth_headers).json()["items"]
    contract = next(c for c in contracts if c["proposal_id"] == proposal["id"])

    return {"job": job, "proposal": proposal, "contract": contract}
