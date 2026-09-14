import uuid

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.orm import Session

from app.db.Session import get_db
from app.dependencies import get_current_user
from app.models.enums import AttachmentResourceType
from app.models.user import User
from app.schemas.attachment import AttachmentDownloadOut, AttachmentOut
from app.services import attachment_service

router = APIRouter(prefix="/api/files", tags=["files"])


@router.post("", response_model=AttachmentOut, status_code=status.HTTP_201_CREATED)
def upload_file(
    resource_type: AttachmentResourceType,
    resource_id: uuid.UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return attachment_service.upload_attachment(db, current_user, resource_type, resource_id, file)


@router.get("", response_model=list[AttachmentOut])
def list_files(
    resource_type: AttachmentResourceType,
    resource_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return attachment_service.list_attachments(db, current_user, resource_type, resource_id)


@router.get("/{attachment_id}", response_model=AttachmentOut)
def get_file(
    attachment_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return attachment_service.get_attachment(db, current_user, attachment_id)


@router.get("/{attachment_id}/download", response_model=AttachmentDownloadOut)
def download_file(
    attachment_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    url, expires_in = attachment_service.get_download_url(db, current_user, attachment_id)
    return AttachmentDownloadOut(url=url, expires_in=expires_in)


@router.delete("/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_file(
    attachment_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    attachment_service.delete_attachment(db, current_user, attachment_id)
