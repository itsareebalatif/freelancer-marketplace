def test_summary_requires_authentication(client):
    response = client.get("/users/summary")
    assert response.status_code in (401, 403)


def test_client_summary_reflects_jobs_and_proposals_received(client, client_auth_headers, freelancer_auth_headers):
    job = client.post(
        "/jobs",
        json={"title": "Build a website", "description": "desc", "budget": "500.00"},
        headers=client_auth_headers,
    ).json()
    client.patch(f"/jobs/{job['id']}", json={"status": "PUBLISHED"}, headers=client_auth_headers)
    client.post(
        f"/jobs/{job['id']}/proposals",
        json={"cover_letter": "I can do this", "bid_amount": "500.00", "estimated_duration": "2 weeks"},
        headers=freelancer_auth_headers,
    )

    response = client.get("/users/summary", headers=client_auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["role"] == "CLIENT"
    assert body["jobs_by_status"] == {"PUBLISHED": 1}
    assert body["proposals_received"] == 1
    assert body["contracts_by_status"] == {}
    assert body["proposals_by_status"] is None
    assert body["bio"] is None


def test_freelancer_summary_reflects_proposals_and_profile(client, client_auth_headers, freelancer_auth_headers):
    client.post("/profiles", json={"bio": "I build things", "skill_ids": []}, headers=freelancer_auth_headers)

    job = client.post(
        "/jobs",
        json={"title": "Build a website", "description": "desc", "budget": "500.00"},
        headers=client_auth_headers,
    ).json()
    client.patch(f"/jobs/{job['id']}", json={"status": "PUBLISHED"}, headers=client_auth_headers)
    client.post(
        f"/jobs/{job['id']}/proposals",
        json={"cover_letter": "I can do this", "bid_amount": "500.00", "estimated_duration": "2 weeks"},
        headers=freelancer_auth_headers,
    )

    response = client.get("/users/summary", headers=freelancer_auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["role"] == "FREELANCER"
    assert body["proposals_by_status"] == {"PENDING": 1}
    assert body["bio"] == "I build things"
    assert body["jobs_by_status"] is None
    assert body["proposals_received"] is None


def test_summary_reflects_active_contract_for_both_parties(client, active_contract, client_auth_headers, freelancer_auth_headers):
    client_summary = client.get("/users/summary", headers=client_auth_headers).json()
    freelancer_summary = client.get("/users/summary", headers=freelancer_auth_headers).json()

    assert client_summary["contracts_by_status"] == {"ACTIVE": 1}
    assert freelancer_summary["contracts_by_status"] == {"ACTIVE": 1}


def test_summary_reflects_average_rating(client, active_contract, client_auth_headers, freelancer_auth_headers):
    contract_id = active_contract["contract"]["id"]
    milestone = client.post(
        f"/contracts/{contract_id}/milestones",
        json={"title": "Design phase", "amount": "500.00"},
        headers=client_auth_headers,
    ).json()
    client.patch(f"/milestones/{milestone['id']}", json={"status": "SUBMITTED"}, headers=freelancer_auth_headers)
    client.patch(f"/milestones/{milestone['id']}", json={"status": "APPROVED"}, headers=client_auth_headers)
    client.patch(f"/contracts/{contract_id}", json={"status": "COMPLETED"}, headers=client_auth_headers)

    client.post(
        f"/contracts/{contract_id}/reviews",
        json={"rating": 4, "comment": "Great freelancer"},
        headers=client_auth_headers,
    )

    freelancer_summary = client.get("/users/summary", headers=freelancer_auth_headers).json()
    assert freelancer_summary["average_rating"] == 4.0

    client_summary = client.get("/users/summary", headers=client_auth_headers).json()
    assert client_summary["average_rating"] is None
