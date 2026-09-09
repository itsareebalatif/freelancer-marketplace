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


def list_jobs(db: Session, *, page: int, page_size: int, search=None, skill_id=None, sort_by="newest"):
    return JobRepository(db).list_published(
        page=page, page_size=page_size, search=search, skill_id=skill_id, sort_by=sort_by
    )


def list_my_jobs(db: Session, user: User, *, page: int, page_size: int):
    return JobRepository(db).list_by_client(user.id, page=page, page_size=page_size)


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


def update_job(db: Session, user: User, job_id, data: JobUpdate) -> Job:
    job = _get_owned_job(db, user, job_id)
    if job.status in NOT_EDITABLE_STATUSES:
        raise ConflictError("A closed or completed job can't be edited", code="JOB_NOT_EDITABLE")

    changes = data.model_dump(exclude_unset=True)
    job = JobRepository(db).update(job, **changes)
    logger.info("Job %s updated by client %s: %s", job.id, user.id, list(changes.keys()))
    return job


def publish_job(db: Session, user: User, job_id) -> Job:
    job = _get_owned_job(db, user, job_id)
    if job.status != JobStatus.DRAFT:
        raise ConflictError("Only a draft job can be published", code="INVALID_JOB_STATUS_TRANSITION")

    job = JobRepository(db).update(job, status=JobStatus.PUBLISHED)
    logger.info("Job %s published by client %s", job.id, user.id)
    return job


def close_job(db: Session, user: User, job_id) -> Job:
    job = _get_owned_job(db, user, job_id)
    if job.status in NOT_EDITABLE_STATUSES:
        raise ConflictError("Job is already closed or completed", code="INVALID_JOB_STATUS_TRANSITION")

    job = JobRepository(db).update(job, status=JobStatus.CLOSED)
    logger.info("Job %s closed by client %s", job.id, user.id)
    return job


def add_skill(db: Session, user: User, job_id, skill_id) -> Job:
    job = _get_owned_job(db, user, job_id)
    skill = SkillRepository(db).get_by_id(skill_id)
    if skill is None:
        raise NotFoundError("Skill not found", code="SKILL_NOT_FOUND")

    job = JobRepository(db).add_skill(job, skill)
    logger.info("Skill %s added to job %s", skill_id, job.id)
    return job


def remove_skill(db: Session, user: User, job_id, skill_id) -> Job:
    job = _get_owned_job(db, user, job_id)
    skill = SkillRepository(db).get_by_id(skill_id)
    if skill is None:
        raise NotFoundError("Skill not found", code="SKILL_NOT_FOUND")

    job = JobRepository(db).remove_skill(job, skill)
    logger.info("Skill %s removed from job %s", skill_id, job.id)
    return job
