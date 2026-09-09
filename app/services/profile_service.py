import logging

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.models.profile import FreelancerProfile
from app.models.user import User
from app.repositories.profile_repo import ProfileRepository
from app.repositories.skill_repo import SkillRepository
from app.schemas.profile import FreelancerProfileCreate, FreelancerProfileUpdate

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
    profile = ProfileRepository(db).update(profile, **changes)
    logger.info("Freelancer profile updated for user %s: %s", user.id, list(changes.keys()))
    return profile


def add_skill(db: Session, user: User, skill_id) -> FreelancerProfile:
    profile = _get_owned_profile(db, user)
    skill = SkillRepository(db).get_by_id(skill_id)
    if skill is None:
        raise NotFoundError("Skill not found", code="SKILL_NOT_FOUND")

    profile = ProfileRepository(db).add_skill(profile, skill)
    logger.info("Skill %s added to profile of user %s", skill_id, user.id)
    return profile


def remove_skill(db: Session, user: User, skill_id) -> FreelancerProfile:
    profile = _get_owned_profile(db, user)
    skill = SkillRepository(db).get_by_id(skill_id)
    if skill is None:
        raise NotFoundError("Skill not found", code="SKILL_NOT_FOUND")

    profile = ProfileRepository(db).remove_skill(profile, skill)
    logger.info("Skill %s removed from profile of user %s", skill_id, user.id)
    return profile
