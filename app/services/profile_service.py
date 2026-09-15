import logging

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.models.enums import AttachmentResourceType
from app.models.profile import FreelancerProfile
from app.models.user import User
from app.repositories.profile_repo import ProfileRepository
from app.schemas.profile import FreelancerProfileCreate, FreelancerProfileUpdate
from app.services import attachment_service

logger = logging.getLogger(__name__)


def create_profile(db: Session, user: User, data: FreelancerProfileCreate) -> FreelancerProfile:
    profiles = ProfileRepository(db)
    if profiles.get_by_user_id(user.id) is not None:
        logger.warning("Profile creation rejected — user %s already has one", user.id)
        raise ConflictError("You already have a freelancer profile", code="PROFILE_ALREADY_EXISTS")

    profile = profiles.create(user_id=user.id, **data.model_dump())
    logger.info("Freelancer profile created for user %s", user.id)
    return profile


def _get_owned_profile(db: Session, user: User) -> FreelancerProfile:
    profile = ProfileRepository(db).get_by_user_id(user.id)
    if profile is None:
        raise NotFoundError("You don't have a freelancer profile yet", code="PROFILE_NOT_FOUND")
    return profile


def get_my_profile(db: Session, user: User) -> FreelancerProfile:
    return _get_owned_profile(db, user)


def update_profile(db: Session, user: User, data: FreelancerProfileUpdate) -> FreelancerProfile:
    profile = _get_owned_profile(db, user)
    changes = data.model_dump(exclude_unset=True)

    if changes:
        profile = ProfileRepository(db).update(profile, **changes)
        logger.info("Freelancer profile updated for user %s: %s", user.id, list(changes.keys()))

    return profile


def upload_avatar(db: Session, user: User, file) -> FreelancerProfile:
    profile = _get_owned_profile(db, user)
    attachment = attachment_service.upload_attachment(
        db, user, AttachmentResourceType.PROFILE, profile.id, file
    )
    profile = ProfileRepository(db).update(profile, avatar_attachment_id=attachment.id)
    logger.info("Avatar uploaded for user %s (attachment %s)", user.id, attachment.id)
    return profile
