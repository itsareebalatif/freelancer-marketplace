from app.models.job import Job
from app.models.enums import BudgetType, ExperienceLevel, JobStatus, LocationType
from app.repositories.base import BaseRepository


class JobRepository(BaseRepository):
    def get_by_id(self, job_id) -> Job | None:
        return self.db.query(Job).filter(Job.id == job_id).first()

    def create(self, *, client_id, **fields) -> Job:
        return self.add(Job(client_id=client_id, **fields))

    def update(self, job: Job, **fields) -> Job:
        for key, value in fields.items():
            setattr(job, key, value)
        self.db.commit()
        self.db.refresh(job)
        return job

    def set_skills(self, job: Job, skills: list) -> Job:
        job.skills = skills
        self.db.commit()
        self.db.refresh(job)
        return job

    def _paginate(self, query, page: int, page_size: int):
        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()
        return items, total

    def list_published(
        self,
        *,
        page: int,
        page_size: int,
        search: str | None = None,
        skill_id=None,
        category: str | None = None,
        budget_type: BudgetType | None = None,
        experience_level: ExperienceLevel | None = None,
        location_type: LocationType | None = None,
        sort_by: str = "newest",
    ):
        query = self.db.query(Job).filter(Job.status == JobStatus.PUBLISHED)

        if search:
            query = query.filter(Job.title.ilike(f"%{search}%"))

        if skill_id is not None:
            query = query.filter(Job.skills.any(id=skill_id))

        if category:
            query = query.filter(Job.category.ilike(category))

        if budget_type is not None:
            query = query.filter(Job.budget_type == budget_type)

        if experience_level is not None:
            query = query.filter(Job.experience_level == experience_level)

        if location_type is not None:
            query = query.filter(Job.location_type == location_type)

        if sort_by == "budget_asc":
            query = query.order_by(Job.budget.asc())
        elif sort_by == "budget_desc":
            query = query.order_by(Job.budget.desc())
        else:
            query = query.order_by(Job.created_at.desc())

        return self._paginate(query, page, page_size)

    def list_by_client(self, client_id, *, page: int, page_size: int, status: JobStatus | None = None):
        query = self.db.query(Job).filter(Job.client_id == client_id)
        if status is not None:
            query = query.filter(Job.status == status)
        query = query.order_by(Job.created_at.desc())
        return self._paginate(query, page, page_size)
