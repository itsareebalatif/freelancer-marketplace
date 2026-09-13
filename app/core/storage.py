import uuid
from pathlib import Path

from fastapi import UploadFile

from app.core.exceptions import ConflictError

UPLOAD_ROOT = Path("uploads")
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_DOCUMENT_TYPES = {"application/pdf", "image/jpeg", "image/png"}


def save_upload(file: UploadFile, subfolder: str, allowed_types: set[str]) -> str:
    if file.content_type not in allowed_types:
        raise ConflictError(f"Unsupported file type: {file.content_type}", code="UNSUPPORTED_FILE_TYPE")

    contents = file.file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise ConflictError("File too large (max 5MB)", code="FILE_TOO_LARGE")

    folder = UPLOAD_ROOT / subfolder
    folder.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid.uuid4()}{Path(file.filename).suffix}"
    (folder / filename).write_bytes(contents)

    return f"/uploads/{subfolder}/{filename}"
