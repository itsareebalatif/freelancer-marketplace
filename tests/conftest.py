from datetime import timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import DateTime, create_engine
from sqlalchemy.dialects.sqlite.base import DATETIME as SQLiteDateTime
from sqlalchemy.dialects.sqlite.pysqlite import SQLiteDialect_pysqlite
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401  ensures all models are registered on Base.metadata
from app.db.base import Base
from app.db.Session import get_db
from app.main import app


# SQLite has no native timezone-aware datetime type, so it hands back naive
# datetimes for columns declared with DateTime(timezone=True). Postgres (used
# in production) doesn't have this problem. Patch the sqlite dialect so
# values read back in tests carry UTC tzinfo, matching real Postgres
# behaviour and keeping app code free of test-only workarounds.
class _TZAwareSQLiteDateTime(SQLiteDateTime):
    def result_processor(self, dialect, coltype):
        base_processor = super().result_processor(dialect, coltype)

        def process(value):
            if base_processor is not None:
                value = base_processor(value)
            if value is not None and value.tzinfo is None:
                value = value.replace(tzinfo=timezone.utc)
            return value

        return process


SQLiteDialect_pysqlite.colspecs = {
    **SQLiteDialect_pysqlite.colspecs,
    DateTime: _TZAwareSQLiteDateTime,
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


def _register_and_login(client, email: str, password: str, role: str) -> dict:
    client.post("/auth/register", json={"email": email, "password": password, "role": role})
    response = client.post("/auth/login", json={"email": email, "password": password})
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def client_auth_headers(client):
    return _register_and_login(client, "client@example.com", "password123", "CLIENT")


@pytest.fixture()
def freelancer_auth_headers(client):
    return _register_and_login(client, "freelancer@example.com", "password123", "FREELANCER")


@pytest.fixture()
def active_contract(client, client_auth_headers, freelancer_auth_headers):
    """Builds a full job -> proposal -> accepted contract chain.

    Reused by the jobs/proposals/contracts/milestones/reviews tests so each
    one doesn't have to repeat this setup by hand.
    """
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
