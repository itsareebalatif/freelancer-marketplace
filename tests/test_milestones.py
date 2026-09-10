def _create_milestone(client, contract_id, client_auth_headers):
    response = client.post(
        f"/contracts/{contract_id}/milestones",
        json={"title": "Design phase", "amount": "500.00"},
        headers=client_auth_headers,
    )
    return response.json()


def test_client_can_create_milestone(client, active_contract, client_auth_headers):
    contract_id = active_contract["contract"]["id"]

    response = client.post(
        f"/contracts/{contract_id}/milestones",
        json={"title": "Design phase", "amount": "500.00"},
        headers=client_auth_headers,
    )

    assert response.status_code == 201
    assert response.json()["status"] == "PENDING"


def test_freelancer_cannot_create_milestone(client, active_contract, freelancer_auth_headers):
    contract_id = active_contract["contract"]["id"]

    response = client.post(
        f"/contracts/{contract_id}/milestones",
        json={"title": "Design phase", "amount": "500.00"},
        headers=freelancer_auth_headers,
    )

    assert response.status_code == 403


def test_full_milestone_lifecycle(client, active_contract, client_auth_headers, freelancer_auth_headers):
    contract_id = active_contract["contract"]["id"]
    milestone = _create_milestone(client, contract_id, client_auth_headers)

    submitted = client.post(
        f"/milestones/{milestone['id']}/submit", headers=freelancer_auth_headers
    )
    assert submitted.status_code == 200
    assert submitted.json()["status"] == "SUBMITTED"

    approved = client.post(f"/milestones/{milestone['id']}/approve", headers=client_auth_headers)
    assert approved.status_code == 200
    assert approved.json()["status"] == "APPROVED"


def test_cannot_approve_a_milestone_that_was_never_submitted(
    client, active_contract, client_auth_headers
):
    contract_id = active_contract["contract"]["id"]
    milestone = _create_milestone(client, contract_id, client_auth_headers)

    response = client.post(f"/milestones/{milestone['id']}/approve", headers=client_auth_headers)
    assert response.status_code == 409


def test_completing_contract_after_all_milestones_approved(
    client, active_contract, client_auth_headers, freelancer_auth_headers
):
    contract_id = active_contract["contract"]["id"]
    milestone = _create_milestone(client, contract_id, client_auth_headers)

    client.post(f"/milestones/{milestone['id']}/submit", headers=freelancer_auth_headers)
    client.post(f"/milestones/{milestone['id']}/approve", headers=client_auth_headers)

    response = client.post(f"/contracts/{contract_id}/complete", headers=client_auth_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "COMPLETED"
