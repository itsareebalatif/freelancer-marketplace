import hashlib
import logging
import uuid

from fastapi import UploadFile
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core import supabase_storage
from app.core.config import settings
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.core.supabase_storage import StorageError
from app.models.attachment import Attachment
from app.models.enums import AttachmentResourceType
from app.models.user import User
from app.repositories.attachment_repo import AttachmentRepository
from app.repositories.contract_repo import ContractRepository
from app.repositories.job_repo import JobRepository
from app.repositories.milestone_repo import MilestoneRepository
from app.repositories.profile_repo import ProfileRepository
from app.repositories.proposal_repo import ProposalRepository

logger = logging.getLogger(__name__)

# MIME type -> file extension used for the generated storage path. The original
# filename the client sent is kept only as display metadata — it never touches
# the storage path, which is what keeps path traversal / unsafe filenames off the
# table entirely rather than something we have to sanitize.
_EXTENSIONS = {
    "application/pdf": ".pdf",
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}

_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
_DOCUMENT_TYPES = {"application/pdf", "image/jpeg", "image/png"}

# What each resource accepts — a profile avatar only makes sense as an image, while
# job/proposal/contract/milestone attachments are documents (PDF or a scanned image).
ALLOWED_TYPES_BY_RESOURCE = {
    AttachmentResourceType.PROFILE: _IMAGE_TYPES,
    AttachmentResourceType.JOB: _DOCUMENT_TYPES,
    AttachmentResourceType.PROPOSAL: _DOCUMENT_TYPES,
    AttachmentResourceType.CONTRACT: _DOCUMENT_TYPES,
    AttachmentResourceType.MILESTONE: _DOCUMENT_TYPES,
}

MAX_ATTACHMENT_SIZE = 5 * 1024 * 1024  # 5MB
_READ_CHUNK_SIZE = 1024 * 1024  # read in 1MB chunks so an oversized upload is rejected without buffering it all


def _read_and_validate(file: UploadFile, resource_type: AttachmentResourceType) -> tuple[bytes, str]:
    if file.content_type not in ALLOWED_TYPES_BY_RESOURCE[resource_type]:
        raise ConflictError(f"Unsupported file type: {file.content_type}", code="UNSUPPORTED_FILE_TYPE")

    hasher = hashlib.sha256()
    chunks = []
    total_size = 0
    while True:
        chunk = file.file.read(_READ_CHUNK_SIZE)
        if not chunk:
            break
        total_size += len(chunk)
        if total_size > MAX_ATTACHMENT_SIZE:
            raise ConflictError("File too large (max 5MB)", code="FILE_TOO_LARGE")
        hasher.update(chunk)
        chunks.append(chunk)

    return b"".join(chunks), hasher.hexdigest()


def _resolve_participants(db: Session, resource_type: AttachmentResourceType, resource_id) -> set:
    """The user ids allowed to see/attach files on a resource. Membership here —
    not just being logged in — is what authorization is checked against."""
    if resource_type == AttachmentResourceType.JOB:
        job = JobRepository(db).get_by_id(resource_id)
        if job is None:
            raise NotFoundError("Job not found", code="JOB_NOT_FOUND")
        return {job.client_id}

    if resource_type == AttachmentResourceType.PROPOSAL:
        proposal = ProposalRepository(db).get_by_id(resource_id)
        if proposal is None:
            raise NotFoundError("Proposal not found", code="PROPOSAL_NOT_FOUND")
        job = JobRepository(db).get_by_id(proposal.job_id)
        participants = {proposal.freelancer_id}
        if job is not None:
            participants.add(job.client_id)
        return participants

    if resource_type == AttachmentResourceType.CONTRACT:
        contract = ContractRepository(db).get_by_id(resource_id)
        if contract is None:
            raise NotFoundError("Contract not found", code="CONTRACT_NOT_FOUND")
        return {contract.client_id, contract.freelancer_id}

    if resource_type == AttachmentResourceType.MILESTONE:
        milestone = MilestoneRepository(db).get_by_id(resource_id)
        if milestone is None:
            raise NotFoundError("Milestone not found", code="MILESTONE_NOT_FOUND")
        contract = ContractRepository(db).get_by_id(milestone.contract_id)
        if contract is None:
            raise NotFoundError("Contract not found", code="CONTRACT_NOT_FOUND")
        return {contract.client_id, contract.freelancer_id}

    if resource_type == AttachmentResourceType.PROFILE:
        profile = ProfileRepository(db).get_by_id(resource_id)
        if profile is None:
            raise NotFoundError("Profile not found", code="PROFILE_NOT_FOUND")
        return {profile.user_id}

    raise NotFoundError("Unknown resource type", code="UNKNOWN_RESOURCE_TYPE")


def _require_participant(db: Session, user: User, resource_type: AttachmentResourceType, resource_id) -> None:
    if user.id not in _resolve_participants(db, resource_type, resource_id):
        raise ForbiddenError("You are not a participant of this resource", code="ATTACHMENT_ACCESS_DENIED")


def upload_attachment(
    db: Session, user: User, resource_type: AttachmentResourceType, resource_id, file: UploadFile
) -> Attachment:
    _require_participant(db, user, resource_type, resource_id)
    content, checksum = _read_and_validate(file, resource_type)

    attachments = AttachmentRepository(db)
    existing = attachments.get_by_checksum(resource_type, resource_id, checksum)
    if existing is not None:
        logger.info("Duplicate upload for %s %s — reusing attachment %s", resource_type, resource_id, existing.id)
        return existing

    extension = _EXTENSIONS[file.content_type]
    storage_key = f"{resource_type.value.lower()}/{resource_id}/{uuid.uuid4().hex}{extension}"

    try:
        supabase_storage.upload_object(storage_key, content, file.content_type)
    except StorageError:
        logger.exception("Storage upload failed for %s", storage_key)
        raise ConflictError("Could not upload the file right now, try again", code="STORAGE_UPLOAD_FAILED")

    try:
        attachment = attachments.create(
            owner_id=user.id,
            resource_type=resource_type,
            resource_id=resource_id,
            original_filename=file.filename or "upload",
            storage_key=storage_key,
            mime_type=file.content_type,
            size_bytes=len(content),
            checksum=checksum,
        )
    except IntegrityError:
        # Lost a race with a concurrent identical upload — the object we just wrote
        # is now a duplicate; remove it and hand back the row that won instead.
        db.rollback()
        _try_delete_storage_object(storage_key)
        existing = attachments.get_by_checksum(resource_type, resource_id, checksum)
        if existing is not None:
            return existing
        raise ConflictError("Duplicate upload, try again", code="DUPLICATE_UPLOAD")
    except Exception:
        # DB write failed after the object was already stored — don't leave an orphan.
        _try_delete_storage_object(storage_key)
        raise

    logger.info("Attachment %s uploaded by %s for %s %s", attachment.id, user.id, resource_type, resource_id)
    return attachment


def _try_delete_storage_object(storage_key: str) -> None:
    try:
        supabase_storage.delete_object(storage_key)
    except StorageError:
        logger.exception("Failed to roll back orphaned storage object %s", storage_key)


def list_attachments(db: Session, user: User, resource_type: AttachmentResourceType, resource_id) -> list[Attachment]:
    _require_participant(db, user, resource_type, resource_id)
    return AttachmentRepository(db).list_for_resource(resource_type, resource_id)


def get_attachment(db: Session, user: User, attachment_id) -> Attachment:
    attachment = AttachmentRepository(db).get_by_id(attachment_id)
    if attachment is None:
        raise NotFoundError("Attachment not found", code="ATTACHMENT_NOT_FOUND")
    _require_participant(db, user, attachment.resource_type, attachment.resource_id)
    return attachment


def get_download_url(db: Session, user: User, attachment_id) -> tuple[str, int]:
    attachment = get_attachment(db, user, attachment_id)
    try:
        url = supabase_storage.create_signed_url(attachment.storage_key, settings.SIGNED_URL_EXPIRY_SECONDS)
    except StorageError:
        logger.exception("Failed to sign URL for attachment %s", attachment.id)
        raise NotFoundError("File is no longer available in storage", code="ATTACHMENT_STORAGE_MISSING")
    return url, settings.SIGNED_URL_EXPIRY_SECONDS


def delete_attachment(db: Session, user: User, attachment_id) -> None:
    attachments = AttachmentRepository(db)
    attachment = attachments.get_by_id(attachment_id)
    if attachment is None:
        raise NotFoundError("Attachment not found", code="ATTACHMENT_NOT_FOUND")

    if attachment.owner_id != user.id:
        raise ForbiddenError("Only the uploader can delete this file", code="NOT_ATTACHMENT_OWNER")

    try:
        supabase_storage.delete_object(attachment.storage_key)
    except StorageError:
        logger.exception("Storage delete failed for %s", attachment.storage_key)
        raise ConflictError("Could not delete the file right now, try again", code="STORAGE_DELETE_FAILED")

    attachments.delete(attachment)
    logger.info("Attachment %s deleted by %s", attachment.id, user.id)
