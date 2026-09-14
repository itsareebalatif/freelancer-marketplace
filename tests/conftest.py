from datetime import timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import DateTime, create_engine
from sqlalchemy.dialects.sqlite.base import DATETIME as SQLiteDateTime
from sqlalchemy.dialects.sqlite.pysqlite import SQLiteDialect_pysqlite
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
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
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    Base.metadata.create_all(engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


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
    return register_and_login(client, "client@example.com", "password123", "CLIENT")


@pytest.fixture()
def freelancer_auth_headers(client):
    return register_and_login(client, "freelancer@example.com", "password123", "FREELANCER")


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
