import logging

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError
from app.models.profile import Skill
from app.repositories.skill_repo import SkillRepository
from app.schemas.profile import SkillCreate

logger = logging.getLogger(__name__)


def list_skills(db: Session) -> list[Skill]:
    return SkillRepository(db).list_all()


def create_skill(db: Session, data: SkillCreate) -> Skill:
    skills = SkillRepository(db)
    if skills.get_by_name(data.name) is not None:
        logger.warning("Skill creation rejected — already exists: %s", data.name)
        raise ConflictError("Skill already exists", code="SKILL_ALREADY_EXISTS")

    skill = skills.create(name=data.name)
    logger.info("New skill created: %s (%s)", skill.name, skill.id)
    return skill
