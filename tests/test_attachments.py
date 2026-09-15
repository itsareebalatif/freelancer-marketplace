import app.core.supabase_storage as supabase_storage


def _second_freelancer_headers(client):
    client.post(
        "/auth/register",
        json={"email": "other-freelancer@example.com", "password": "Password123!", "role": "FREELANCER"},
    )
    login = client.post(
        "/auth/login", json={"email": "other-freelancer@example.com", "password": "Password123!"}
    )
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_participant_can_upload_and_list_contract_attachment(client, active_contract, client_auth_headers):
    contract_id = active_contract["contract"]["id"]

    upload = client.post(
        "/api/files",
        params={"resource_type": "CONTRACT", "resource_id": contract_id},
        files={"file": ("agreement.pdf", b"contract bytes", "application/pdf")},
        headers=client_auth_headers,
    )
    assert upload.status_code == 201
    body = upload.json()
    assert body["original_filename"] == "agreement.pdf"
    assert body["mime_type"] == "application/pdf"
    assert body["size_bytes"] == len(b"contract bytes")
    assert "storage_key" not in body  # internal path is never exposed

    listing = client.get(
        "/api/files", params={"resource_type": "CONTRACT", "resource_id": contract_id}, headers=client_auth_headers
    )
    assert listing.status_code == 200
    assert len(listing.json()) == 1


def test_non_participant_cannot_upload_or_list(client, active_contract):
    contract_id = active_contract["contract"]["id"]
    outsider = _second_freelancer_headers(client)

    upload = client.post(
        "/api/files",
        params={"resource_type": "CONTRACT", "resource_id": contract_id},
        files={"file": ("agreement.pdf", b"bytes", "application/pdf")},
        headers=outsider,
    )
    assert upload.status_code == 403

    listing = client.get(
        "/api/files", params={"resource_type": "CONTRACT", "resource_id": contract_id}, headers=outsider
    )
    assert listing.status_code == 403


def test_upload_requires_authentication(client, active_contract):
    contract_id = active_contract["contract"]["id"]

    response = client.post(
        "/api/files",
        params={"resource_type": "CONTRACT", "resource_id": contract_id},
        files={"file": ("agreement.pdf", b"bytes", "application/pdf")},
    )
    assert response.status_code in (401, 403)


def test_freelancer_cannot_access_another_freelancers_profile_attachment(
    client, freelancer_auth_headers
):
    profile = client.post("/profiles", json={"bio": "hi"}, headers=freelancer_auth_headers).json()
    avatar = client.post(
        "/profiles/avatar",
        files={"file": ("me.png", b"png bytes", "image/png")},
        headers=freelancer_auth_headers,
    ).json()
    attachment_id = avatar["avatar_attachment_id"]

    outsider = _second_freelancer_headers(client)

    get_response = client.get(f"/api/files/{attachment_id}", headers=outsider)
    assert get_response.status_code == 403

    download_response = client.get(f"/api/files/{attachment_id}/download", headers=outsider)
    assert download_response.status_code == 403

    delete_response = client.delete(f"/api/files/{attachment_id}", headers=outsider)
    assert delete_response.status_code == 403


def test_client_cannot_access_unrelated_contract_files(client, active_contract, client_auth_headers):
    contract_id = active_contract["contract"]["id"]
    client.post(
        "/api/files",
        params={"resource_type": "CONTRACT", "resource_id": contract_id},
        files={"file": ("agreement.pdf", b"bytes", "application/pdf")},
        headers=client_auth_headers,
    )

    other_client = _second_client_headers(client)
    response = client.get(
        "/api/files", params={"resource_type": "CONTRACT", "resource_id": contract_id}, headers=other_client
    )
    assert response.status_code == 403


def _second_client_headers(client):
    client.post(
        "/auth/register",
        json={"email": "other-client@example.com", "password": "Password123!", "role": "CLIENT"},
    )
    login = client.post("/auth/login", json={"email": "other-client@example.com", "password": "Password123!"})
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_invalid_file_type_rejected(client, active_contract, client_auth_headers):
    contract_id = active_contract["contract"]["id"]

    response = client.post(
        "/api/files",
        params={"resource_type": "CONTRACT", "resource_id": contract_id},
        files={"file": ("script.exe", b"MZ...", "application/x-msdownload")},
        headers=client_auth_headers,
    )
    assert response.status_code == 409


def test_avatar_must_be_an_image_not_a_document(client, freelancer_auth_headers):
    client.post("/profiles", json={"bio": "hi"}, headers=freelancer_auth_headers)

    response = client.post(
        "/profiles/avatar",
        files={"file": ("resume.pdf", b"pdf bytes", "application/pdf")},
        headers=freelancer_auth_headers,
    )
    assert response.status_code == 409


def test_oversized_file_rejected(client, active_contract, client_auth_headers):
    contract_id = active_contract["contract"]["id"]
    oversized = b"x" * (5 * 1024 * 1024 + 1)

    response = client.post(
        "/api/files",
        params={"resource_type": "CONTRACT", "resource_id": contract_id},
        files={"file": ("big.pdf", oversized, "application/pdf")},
        headers=client_auth_headers,
    )
    assert response.status_code == 409


def test_missing_attachment_returns_404(client, client_auth_headers):
    fake_id = "00000000-0000-0000-0000-000000000000"

    assert client.get(f"/api/files/{fake_id}", headers=client_auth_headers).status_code == 404
    assert client.get(f"/api/files/{fake_id}/download", headers=client_auth_headers).status_code == 404
    assert client.delete(f"/api/files/{fake_id}", headers=client_auth_headers).status_code == 404


def test_duplicate_upload_reuses_existing_attachment(client, active_contract, client_auth_headers, mock_storage):
    contract_id = active_contract["contract"]["id"]
    payload = {
        "resource_type": "CONTRACT",
        "resource_id": contract_id,
    }
    file_args = {"file": ("agreement.pdf", b"identical bytes", "application/pdf")}

    first = client.post("/api/files", params=payload, files=file_args, headers=client_auth_headers)
    second = client.post("/api/files", params=payload, files=file_args, headers=client_auth_headers)

    assert first.json()["id"] == second.json()["id"]
    assert len(mock_storage) == 1  # only one object actually written to storage

    listing = client.get("/api/files", params=payload, headers=client_auth_headers).json()
    assert len(listing) == 1


def test_download_returns_a_signed_url(client, active_contract, client_auth_headers):
    contract_id = active_contract["contract"]["id"]
    upload = client.post(
        "/api/files",
        params={"resource_type": "CONTRACT", "resource_id": contract_id},
        files={"file": ("agreement.pdf", b"bytes", "application/pdf")},
        headers=client_auth_headers,
    ).json()

    response = client.get(f"/api/files/{upload['id']}/download", headers=client_auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["url"].startswith("https://fake-storage.test/")
    assert body["expires_in"] == 300


def test_uploader_can_delete_and_file_is_gone_after(client, active_contract, client_auth_headers, mock_storage):
    contract_id = active_contract["contract"]["id"]
    upload = client.post(
        "/api/files",
        params={"resource_type": "CONTRACT", "resource_id": contract_id},
        files={"file": ("agreement.pdf", b"bytes", "application/pdf")},
        headers=client_auth_headers,
    ).json()
    assert len(mock_storage) == 1

    delete_response = client.delete(f"/api/files/{upload['id']}", headers=client_auth_headers)
    assert delete_response.status_code == 204
    assert len(mock_storage) == 0

    assert client.get(f"/api/files/{upload['id']}", headers=client_auth_headers).status_code == 404


def test_non_uploader_participant_cannot_delete(client, active_contract, client_auth_headers, freelancer_auth_headers):
    contract_id = active_contract["contract"]["id"]
    upload = client.post(
        "/api/files",
        params={"resource_type": "CONTRACT", "resource_id": contract_id},
        files={"file": ("agreement.pdf", b"bytes", "application/pdf")},
        headers=client_auth_headers,
    ).json()

    response = client.delete(f"/api/files/{upload['id']}", headers=freelancer_auth_headers)
    assert response.status_code == 403


def test_storage_failure_on_upload_leaves_no_orphan_row(client, active_contract, client_auth_headers):
    # Patched (and restored) directly rather than via the `monkeypatch` fixture:
    # that fixture is shared with the autouse mock_storage/mock_email_provider
    # fixtures in this same test, so `monkeypatch.undo()` here would revert those
    # too instead of just this one function.
    original_upload = supabase_storage.upload_object

    def failing_upload(storage_key, content, content_type):
        raise supabase_storage.StorageError("simulated outage")

    supabase_storage.upload_object = failing_upload
    try:
        contract_id = active_contract["contract"]["id"]
        response = client.post(
            "/api/files",
            params={"resource_type": "CONTRACT", "resource_id": contract_id},
            files={"file": ("agreement.pdf", b"bytes", "application/pdf")},
            headers=client_auth_headers,
        )
        assert response.status_code == 409
    finally:
        supabase_storage.upload_object = original_upload

    listing = client.get(
        "/api/files", params={"resource_type": "CONTRACT", "resource_id": contract_id}, headers=client_auth_headers
    )
    assert listing.json() == []


def test_storage_failure_on_delete_keeps_the_row(client, active_contract, client_auth_headers):
    contract_id = active_contract["contract"]["id"]
    upload = client.post(
        "/api/files",
        params={"resource_type": "CONTRACT", "resource_id": contract_id},
        files={"file": ("agreement.pdf", b"bytes", "application/pdf")},
        headers=client_auth_headers,
    ).json()

    original_delete = supabase_storage.delete_object

    def failing_delete(storage_key):
        raise supabase_storage.StorageError("simulated outage")

    supabase_storage.delete_object = failing_delete
    try:
        response = client.delete(f"/api/files/{upload['id']}", headers=client_auth_headers)
        assert response.status_code == 409
    finally:
        supabase_storage.delete_object = original_delete

    assert client.get(f"/api/files/{upload['id']}", headers=client_auth_headers).status_code == 200


def test_uploading_to_a_nonexistent_resource_returns_404(client, client_auth_headers):
    fake_id = "00000000-0000-0000-0000-000000000000"

    response = client.post(
        "/api/files",
        params={"resource_type": "CONTRACT", "resource_id": fake_id},
        files={"file": ("agreement.pdf", b"bytes", "application/pdf")},
        headers=client_auth_headers,
    )
    assert response.status_code == 404
