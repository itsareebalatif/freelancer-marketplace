import logging

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.models.enums import JobStatus
from app.models.job import Job
from app.models.user import User
from app.repositories.job_repo import JobRepository
from app.repositories.skill_repo import SkillRepository
from app.schemas.job import JobCreate, JobUpdate

logger = logging.getLogger(__name__)

NOT_EDITABLE_STATUSES = (JobStatus.CLOSED, JobStatus.COMPLETED)


def create_job(db: Session, user: User, data: JobCreate) -> Job:
    job = JobRepository(db).create(client_id=user.id, **data.model_dump())
    logger.info("Job %s created by client %s", job.id, user.id)
    return job


def list_jobs(
    db: Session,
    *,
    page: int,
    page_size: int,
    search=None,
    skill_id=None,
    category=None,
    budget_type=None,
    experience_level=None,
    location_type=None,
    sort_by="newest",
):
    return JobRepository(db).list_published(
        page=page,
        page_size=page_size,
        search=search,
        skill_id=skill_id,
        category=category,
        budget_type=budget_type,
        experience_level=experience_level,
        location_type=location_type,
        sort_by=sort_by,
    )


def list_my_jobs(db: Session, user: User, *, page: int, page_size: int, status=None):
    return JobRepository(db).list_by_client(user.id, page=page, page_size=page_size, status=status)


def get_job(db: Session, job_id) -> Job:
    job = JobRepository(db).get_by_id(job_id)
    if job is None:
        raise NotFoundError("Job not found", code="JOB_NOT_FOUND")
    return job


def _get_owned_job(db: Session, user: User, job_id) -> Job:
    job = get_job(db, job_id)
    if job.client_id != user.id:
        raise ForbiddenError("You don't own this job", code="NOT_JOB_OWNER")
    return job


CLIENT_SETTABLE_STATUSES = (JobStatus.PUBLISHED, JobStatus.CLOSED)


def _apply_status_transition(job: Job, new_status: JobStatus) -> dict:
    if new_status not in CLIENT_SETTABLE_STATUSES:
        raise ConflictError(
            "Status can only be set to PUBLISHED or CLOSED — IN_PROGRESS and COMPLETED are "
            "set automatically when a proposal is accepted or a contract is completed",
            code="STATUS_NOT_CLIENT_SETTABLE",
        )

    if new_status == JobStatus.PUBLISHED and job.status != JobStatus.DRAFT:
        raise ConflictError("Only a draft job can be published", code="INVALID_JOB_STATUS_TRANSITION")

    if new_status == JobStatus.CLOSED and job.status in NOT_EDITABLE_STATUSES:
        raise ConflictError("Job is already closed or completed", code="INVALID_JOB_STATUS_TRANSITION")

    return {"status": new_status}


def update_job(db: Session, user: User, job_id, data: JobUpdate) -> Job:
    job = _get_owned_job(db, user, job_id)

    changes = data.model_dump(exclude_unset=True)
    new_status = changes.pop("status", None)
    skill_ids = changes.pop("skill_ids", None)

    if changes:
        if job.status in NOT_EDITABLE_STATUSES:
            raise ConflictError("A closed or completed job can't be edited", code="JOB_NOT_EDITABLE")
        job = JobRepository(db).update(job, **changes)
        logger.info("Job %s updated by client %s: %s", job.id, user.id, list(changes.keys()))

    if new_status is not None:
        job = JobRepository(db).update(job, **_apply_status_transition(job, new_status))
        logger.info("Job %s status changed to %s by client %s", job.id, new_status, user.id)

    if skill_ids is not None:
        job = _replace_skills(db, job, skill_ids)
        logger.info("Job %s skills set to %s by client %s", job.id, skill_ids, user.id)

    return job


def _replace_skills(db: Session, job: Job, skill_ids: list) -> Job:
    skills = []
    for skill_id in skill_ids:
        skill = SkillRepository(db).get_by_id(skill_id)
        if skill is None:
            raise NotFoundError(f"Skill {skill_id} not found", code="SKILL_NOT_FOUND")
        skills.append(skill)

    return JobRepository(db).set_skills(job, skills)
