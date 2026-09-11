def _publish_job(client, client_auth_headers):
    job = client.post(
        "/jobs",
        json={"title": "Build a website", "description": "Simple landing page", "budget": "500.00"},
        headers=client_auth_headers,
    ).json()
    client.patch(f"/jobs/{job['id']}", json={"status": "PUBLISHED"}, headers=client_auth_headers)
    return job


def test_freelancer_can_submit_proposal(client, client_auth_headers, freelancer_auth_headers):
    job = _publish_job(client, client_auth_headers)

    response = client.post(
        f"/jobs/{job['id']}/proposals",
        json={"cover_letter": "I can do this", "bid_amount": "500.00", "estimated_duration": "2 weeks"},
        headers=freelancer_auth_headers,
    )

    assert response.status_code == 201
    assert response.json()["status"] == "PENDING"


def test_duplicate_proposal_is_rejected(client, client_auth_headers, freelancer_auth_headers):
    job = _publish_job(client, client_auth_headers)
    payload = {"cover_letter": "I can do this", "bid_amount": "500.00", "estimated_duration": "2 weeks"}

    client.post(f"/jobs/{job['id']}/proposals", json=payload, headers=freelancer_auth_headers)
    second_attempt = client.post(
        f"/jobs/{job['id']}/proposals", json=payload, headers=freelancer_auth_headers
    )

    assert second_attempt.status_code == 409


def test_cannot_submit_proposal_to_unpublished_job(client, client_auth_headers, freelancer_auth_headers):
    draft_job = client.post(
        "/jobs",
        json={"title": "Still a draft", "description": "Not open yet", "budget": "500.00"},
        headers=client_auth_headers,
    ).json()

    response = client.post(
        f"/jobs/{draft_job['id']}/proposals",
        json={"cover_letter": "I can do this", "bid_amount": "500.00", "estimated_duration": "2 weeks"},
        headers=freelancer_auth_headers,
    )

    assert response.status_code == 409


def test_only_job_owner_can_view_its_proposals(client, client_auth_headers, freelancer_auth_headers):
    job = _publish_job(client, client_auth_headers)
    client.post(
        f"/jobs/{job['id']}/proposals",
        json={"cover_letter": "I can do this", "bid_amount": "500.00", "estimated_duration": "2 weeks"},
        headers=freelancer_auth_headers,
    )

    response = client.get(f"/proposals?job_id={job['id']}", headers=freelancer_auth_headers)
    assert response.status_code == 403

    response = client.get(f"/proposals?job_id={job['id']}", headers=client_auth_headers)
    assert response.status_code == 200
    assert response.json()["total"] == 1
