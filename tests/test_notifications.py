import app.services.notification_service as notification_service


def test_registration_sends_welcome_email(client, mock_email_provider):
    client.post(
        "/auth/register",
        json={"email": "new@example.com", "password": "password123", "role": "CLIENT"},
    )

    assert any(m["to"] == "new@example.com" for m in mock_email_provider)


def test_proposal_submission_notifies_client(client, client_auth_headers, freelancer_auth_headers, mock_email_provider):
    job = client.post(
        "/jobs",
        json={"title": "Build a website", "description": "Simple landing page", "budget": "500.00"},
        headers=client_auth_headers,
    ).json()
    client.patch(f"/jobs/{job['id']}", json={"status": "PUBLISHED"}, headers=client_auth_headers)
    mock_email_provider.clear()

    client.post(
        f"/jobs/{job['id']}/proposals",
        json={"cover_letter": "I can do this", "bid_amount": "500.00", "estimated_duration": "2 weeks"},
        headers=freelancer_auth_headers,
    )

    assert any(m["to"] == "client@example.com" for m in mock_email_provider)


def test_notification_history_lists_sent_notifications(client, freelancer_auth_headers):
    response = client.get("/api/notifications", headers=freelancer_auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 1
    assert body["items"][0]["event_type"] == "USER_REGISTERED"
    assert body["items"][0]["status"] == "SENT"


def test_delivery_failure_is_recorded_and_does_not_break_the_request(client, monkeypatch):
    def failing_send_email(*, to, subject, body):
        raise RuntimeError("provider is down")

    monkeypatch.setattr(notification_service, "send_email", failing_send_email)

    response = client.post(
        "/auth/register",
        json={"email": "failcase@example.com", "password": "password123", "role": "CLIENT"},
    )

    assert response.status_code == 201

    headers = {
        "Authorization": "Bearer "
        + client.post(
            "/auth/login", json={"email": "failcase@example.com", "password": "password123"}
        ).json()["access_token"]
    }
    notifications = client.get("/api/notifications", headers=headers).json()["items"]
    assert notifications[0]["status"] == "FAILED"
    assert notifications[0]["last_error"] == "provider is down"


def test_duplicate_event_does_not_send_a_second_email(client_auth_headers, freelancer_auth_headers, client, mock_email_provider, db_session):
    from app.models.enums import NotificationEventType
    from app.models.user import User
    from app.repositories.user_repo import UserRepository

    freelancer = UserRepository(db_session).get_by_email("freelancer@example.com")
    mock_email_provider.clear()

    notification_service.notify(
        db_session, freelancer, NotificationEventType.REVIEW_RECEIVED, {"reviewee_name": "Freelancer"}, resource_id="fixed-id"
    )
    notification_service.notify(
        db_session, freelancer, NotificationEventType.REVIEW_RECEIVED, {"reviewee_name": "Freelancer"}, resource_id="fixed-id"
    )

    assert len(mock_email_provider) == 1


def test_opted_out_event_is_skipped(client, client_auth_headers, freelancer_auth_headers, mock_email_provider):
    client.patch(
        "/api/notifications/preferences",
        json={"preferences": [{"event_type": "PROPOSAL_RECEIVED", "email_enabled": False}]},
        headers=client_auth_headers,
    )

    job = client.post(
        "/jobs",
        json={"title": "Build a website", "description": "Simple landing page", "budget": "500.00"},
        headers=client_auth_headers,
    ).json()
    client.patch(f"/jobs/{job['id']}", json={"status": "PUBLISHED"}, headers=client_auth_headers)
    mock_email_provider.clear()

    client.post(
        f"/jobs/{job['id']}/proposals",
        json={"cover_letter": "I can do this", "bid_amount": "500.00", "estimated_duration": "2 weeks"},
        headers=freelancer_auth_headers,
    )

    assert not any(m["to"] == "client@example.com" for m in mock_email_provider)


def test_preferences_default_to_enabled_for_every_event(client, client_auth_headers):
    response = client.get("/api/notifications/preferences", headers=client_auth_headers)

    assert response.status_code == 200
    prefs = response.json()
    assert all(p["email_enabled"] for p in prefs)


def test_notifications_require_authentication(client):
    response = client.get("/api/notifications")

    assert response.status_code == 403 or response.status_code == 401


def test_test_endpoint_disabled_in_production(client, client_auth_headers, monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "ENV", "production")

    response = client.post("/api/notifications/test", headers=client_auth_headers)

    assert response.status_code == 403
