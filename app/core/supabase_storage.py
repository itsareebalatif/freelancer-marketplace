import requests

from app.core.config import settings


class StorageError(Exception):
    pass


def _object_url(storage_key: str) -> str:
    return f"{settings.SUPABASE_URL}/storage/v1/object/{settings.SUPABASE_STORAGE_BUCKET}/{storage_key}"


def _headers() -> dict:
    return {"Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}"}


def upload_object(storage_key: str, content: bytes, content_type: str) -> None:
    response = requests.post(
        _object_url(storage_key),
        headers={**_headers(), "Content-Type": content_type},
        data=content,
        timeout=30,
    )
    if response.status_code >= 300:
        raise StorageError(f"Upload failed ({response.status_code}): {response.text[:300]}")


def delete_object(storage_key: str) -> None:
    response = requests.delete(_object_url(storage_key), headers=_headers(), timeout=30)
    if response.status_code >= 300 and response.status_code != 404:
        raise StorageError(f"Delete failed ({response.status_code}): {response.text[:300]}")


def create_signed_url(storage_key: str, expires_in: int) -> str:
    response = requests.post(
        f"{settings.SUPABASE_URL}/storage/v1/object/sign/{settings.SUPABASE_STORAGE_BUCKET}/{storage_key}",
        headers=_headers(),
        json={"expiresIn": expires_in},
        timeout=30,
    )
    if response.status_code >= 300:
        raise StorageError(f"Signing failed ({response.status_code}): {response.text[:300]}")

    signed_path = response.json()["signedURL"]
    return f"{settings.SUPABASE_URL}/storage/v1{signed_path}"
