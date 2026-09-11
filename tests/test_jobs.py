def test_client_can_create_job(client, client_auth_headers):
    response = client.post(
        "/jobs",
        json={"title": "Build a website", "description": "Simple landing page", "budget": "500.00"},
        headers=client_auth_headers,
    )
    assert response.status_code == 201
    assert response.json()["title"] == "Build a website"
    assert response.json()["status"] == "DRAFT"


def test_freelancer_cannot_create_job(client, freelancer_auth_headers):
    response = client.post(
        "/jobs",
        json={"title": "Build a website", "description": "Simple landing page", "budget": "500.00"},
        headers=freelancer_auth_headers,
    )
    assert response.status_code == 403


def test_partial_update_only_changes_given_field(client, client_auth_headers):
    job = client.post(
        "/jobs",
        json={"title": "Old Title", "description": "Original description", "budget": "500.00"},
        headers=client_auth_headers,
    ).json()

    updated = client.patch(f"/jobs/{job['id']}", json={"title": "New Title"}, headers=client_auth_headers)

    assert updated.status_code == 200
    assert updated.json()["title"] == "New Title"
    assert updated.json()["description"] == "Original description"


def test_another_client_cannot_update_someone_elses_job(client, client_auth_headers):
    job = client.post(
        "/jobs",
        json={"title": "Old Title", "description": "Original description", "budget": "500.00"},
        headers=client_auth_headers,
    ).json()

    client.post(
        "/auth/register",
        json={"email": "other_client@example.com", "password": "password123", "role": "CLIENT"},
    )
    login = client.post(
        "/auth/login", json={"email": "other_client@example.com", "password": "password123"}
    )
    other_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    response = client.patch(f"/jobs/{job['id']}", json={"title": "Hijacked"}, headers=other_headers)
    assert response.status_code in (403, 404)


def test_list_jobs_only_shows_published(client, client_auth_headers):
    client.post(
        "/jobs",
        json={"title": "Draft Job", "description": "Not published", "budget": "100.00"},
        headers=client_auth_headers,
    )
    published = client.post(
        "/jobs",
        json={"title": "Published Job", "description": "Ready to go", "budget": "100.00"},
        headers=client_auth_headers,
    ).json()
    client.patch(f"/jobs/{published['id']}", json={"status": "PUBLISHED"}, headers=client_auth_headers)

    response = client.get("/jobs")
    titles = [job["title"] for job in response.json()["items"]]

    assert "Published Job" in titles
    assert "Draft Job" not in titles
