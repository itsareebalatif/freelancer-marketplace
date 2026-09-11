def test_accepting_a_proposal_creates_a_contract(client, client_auth_headers, freelancer_auth_headers):
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

    accepted = client.patch(
        f"/proposals/{proposal['id']}", json={"status": "ACCEPTED"}, headers=client_auth_headers
    )
    assert accepted.status_code == 200
    assert accepted.json()["status"] == "ACCEPTED"

    contracts = client.get("/contracts", headers=client_auth_headers).json()["items"]
    assert any(c["proposal_id"] == proposal["id"] for c in contracts)


def test_accepting_one_proposal_rejects_the_others(client, client_auth_headers, freelancer_auth_headers):
    job = client.post(
        "/jobs",
        json={"title": "Build a website", "description": "Simple landing page", "budget": "500.00"},
        headers=client_auth_headers,
    ).json()
    client.patch(f"/jobs/{job['id']}", json={"status": "PUBLISHED"}, headers=client_auth_headers)

    winning = client.post(
        f"/jobs/{job['id']}/proposals",
        json={"cover_letter": "Pick me", "bid_amount": "500.00", "estimated_duration": "2 weeks"},
        headers=freelancer_auth_headers,
    ).json()

    client.post(
        "/auth/register",
        json={"email": "other_freelancer@example.com", "password": "password123", "role": "FREELANCER"},
    )
    other_login = client.post(
        "/auth/login", json={"email": "other_freelancer@example.com", "password": "password123"}
    )
    other_headers = {"Authorization": f"Bearer {other_login.json()['access_token']}"}
    losing = client.post(
        f"/jobs/{job['id']}/proposals",
        json={"cover_letter": "Pick me instead", "bid_amount": "450.00", "estimated_duration": "1 week"},
        headers=other_headers,
    ).json()

    client.patch(f"/proposals/{winning['id']}", json={"status": "ACCEPTED"}, headers=client_auth_headers)

    losing_after = client.get(f"/proposals/{losing['id']}", headers=client_auth_headers).json()
    assert losing_after["status"] == "REJECTED"


def test_only_client_can_complete_contract(client, active_contract, freelancer_auth_headers):
    contract_id = active_contract["contract"]["id"]

    response = client.patch(
        f"/contracts/{contract_id}", json={"status": "COMPLETED"}, headers=freelancer_auth_headers
    )
    assert response.status_code == 403


def test_contract_cannot_complete_with_incomplete_milestones(client, active_contract, client_auth_headers):
    contract_id = active_contract["contract"]["id"]
    client.post(
        f"/contracts/{contract_id}/milestones",
        json={"title": "Design phase", "amount": "500.00"},
        headers=client_auth_headers,
    )

    response = client.patch(
        f"/contracts/{contract_id}", json={"status": "COMPLETED"}, headers=client_auth_headers
    )
    assert response.status_code == 409
