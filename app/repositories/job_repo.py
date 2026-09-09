from app.models.job import Job
from app.models.enums import JobStatus
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

    def add_skill(self, job: Job, skill) -> Job:
        if skill not in job.skills:
            job.skills.append(skill)
            self.db.commit()
            self.db.refresh(job)
        return job

    def remove_skill(self, job: Job, skill) -> Job:
        if skill in job.skills:
            job.skills.remove(skill)
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
        sort_by: str = "newest",
    ):
        query = self.db.query(Job).filter(Job.status == JobStatus.PUBLISHED)

        if search:
            query = query.filter(Job.title.ilike(f"%{search}%"))

        if skill_id is not None:
            query = query.filter(Job.skills.any(id=skill_id))

        if sort_by == "budget_asc":
            query = query.order_by(Job.budget.asc())
        elif sort_by == "budget_desc":
            query = query.order_by(Job.budget.desc())
        else:
            query = query.order_by(Job.created_at.desc())

        return self._paginate(query, page, page_size)

    def list_by_client(self, client_id, *, page: int, page_size: int):
        query = self.db.query(Job).filter(Job.client_id == client_id).order_by(Job.created_at.desc())
        return self._paginate(query, page, page_size)
