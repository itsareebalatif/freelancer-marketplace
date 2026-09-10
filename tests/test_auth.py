def test_register_and_login(client):
    register = client.post(
        "/auth/register",
        json={"email": "a@example.com", "password": "password123", "role": "CLIENT"},
    )
    assert register.status_code == 201
    assert register.json()["email"] == "a@example.com"

    login = client.post(
        "/auth/login", json={"email": "a@example.com", "password": "password123"}
    )
    assert login.status_code == 200
    body = login.json()
    assert "access_token" in body
    assert "refresh_token" not in body
    assert body["email"] == "a@example.com"
    assert body["role"] == "CLIENT"
    assert "refresh_token" in login.cookies


def test_login_wrong_password_rejected(client):
    client.post(
        "/auth/register",
        json={"email": "b@example.com", "password": "password123", "role": "CLIENT"},
    )
    login = client.post(
        "/auth/login", json={"email": "b@example.com", "password": "wrong"}
    )
    assert login.status_code == 401


def test_me_requires_auth_header(client):
    response = client.get("/auth/me")
    assert response.status_code in (401, 403)


def test_me_with_valid_token(client, client_auth_headers):
    response = client.get("/auth/me", headers=client_auth_headers)
    assert response.status_code == 200
    assert response.json()["role"] == "CLIENT"


def test_refresh_rotates_token(client):
    client.post(
        "/auth/register",
        json={"email": "c@example.com", "password": "password123", "role": "FREELANCER"},
    )
    login = client.post(
        "/auth/login", json={"email": "c@example.com", "password": "password123"}
    )
    old_refresh_token = login.cookies["refresh_token"]

    refreshed = client.post("/auth/refresh")
    assert refreshed.status_code == 200
    assert client.cookies["refresh_token"] != old_refresh_token

    client.cookies.set("refresh_token", old_refresh_token)
    reused = client.post("/auth/refresh")
    assert reused.status_code == 401


def test_logout_revokes_refresh_token(client):
    client.post(
        "/auth/register",
        json={"email": "d@example.com", "password": "password123", "role": "CLIENT"},
    )
    login = client.post(
        "/auth/login", json={"email": "d@example.com", "password": "password123"}
    )
    access_token = login.json()["access_token"]

    logout = client.post("/auth/logout", headers={"Authorization": f"Bearer {access_token}"})
    assert logout.status_code == 204

    reused = client.post("/auth/refresh")
    assert reused.status_code == 401
