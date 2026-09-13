def test_freelancer_can_upload_avatar(client, freelancer_auth_headers):
    client.post("/profiles", json={"bio": "I build things"}, headers=freelancer_auth_headers)

    response = client.post(
        "/profiles/avatar",
        files={"file": ("avatar.png", b"fake-png-bytes", "image/png")},
        headers=freelancer_auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["avatar_url"].startswith("/uploads/avatars/")


def test_avatar_upload_rejects_unsupported_file_type(client, freelancer_auth_headers):
    client.post("/profiles", json={"bio": "I build things"}, headers=freelancer_auth_headers)

    response = client.post(
        "/profiles/avatar",
        files={"file": ("resume.pdf", b"fake-pdf-bytes", "application/pdf")},
        headers=freelancer_auth_headers,
    )

    assert response.status_code == 409
