def _complete_contract(client, active_contract, client_auth_headers, freelancer_auth_headers):
    contract_id = active_contract["contract"]["id"]
    milestone = client.post(
        f"/contracts/{contract_id}/milestones",
        json={"title": "Design phase", "amount": "500.00"},
        headers=client_auth_headers,
    ).json()

    client.patch(f"/milestones/{milestone['id']}", json={"status": "SUBMITTED"}, headers=freelancer_auth_headers)
    client.patch(f"/milestones/{milestone['id']}", json={"status": "APPROVED"}, headers=client_auth_headers)
    client.patch(f"/contracts/{contract_id}", json={"status": "COMPLETED"}, headers=client_auth_headers)

    return contract_id


def test_review_rejected_before_contract_is_completed(client, active_contract, client_auth_headers):
    contract_id = active_contract["contract"]["id"]

    response = client.post(
        f"/contracts/{contract_id}/reviews",
        json={"rating": 5, "comment": "Great work"},
        headers=client_auth_headers,
    )

    assert response.status_code == 409


def test_client_and_freelancer_can_each_review_once(
    client, active_contract, client_auth_headers, freelancer_auth_headers
):
    contract_id = _complete_contract(client, active_contract, client_auth_headers, freelancer_auth_headers)

    client_review = client.post(
        f"/contracts/{contract_id}/reviews",
        json={"rating": 5, "comment": "Great freelancer"},
        headers=client_auth_headers,
    )
    freelancer_review = client.post(
        f"/contracts/{contract_id}/reviews",
        json={"rating": 4, "comment": "Great client"},
        headers=freelancer_auth_headers,
    )

    assert client_review.status_code == 201
    assert freelancer_review.status_code == 201


def test_duplicate_review_on_same_contract_is_rejected(
    client, active_contract, client_auth_headers, freelancer_auth_headers
):
    contract_id = _complete_contract(client, active_contract, client_auth_headers, freelancer_auth_headers)

    client.post(
        f"/contracts/{contract_id}/reviews",
        json={"rating": 5, "comment": "Great freelancer"},
        headers=client_auth_headers,
    )
    second_attempt = client.post(
        f"/contracts/{contract_id}/reviews",
        json={"rating": 1, "comment": "Changed my mind"},
        headers=client_auth_headers,
    )

    assert second_attempt.status_code == 409
