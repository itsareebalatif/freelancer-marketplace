from app.models.enums import ProposalStatus
from app.models.proposal import Proposal
from app.repositories.base import BaseRepository


class ProposalRepository(BaseRepository):
    def get_by_id(self, proposal_id) -> Proposal | None:
        return self.db.query(Proposal).filter(Proposal.id == proposal_id).first()

    def get_by_job_and_freelancer(self, job_id, freelancer_id) -> Proposal | None:
        return (
            self.db.query(Proposal)
            .filter(Proposal.job_id == job_id, Proposal.freelancer_id == freelancer_id)
            .first()
        )

    def create(self, *, job_id, freelancer_id, **fields) -> Proposal:
        return self.add(Proposal(job_id=job_id, freelancer_id=freelancer_id, **fields))

    def list_pending_for_job_excluding(self, job_id, exclude_proposal_id) -> list[Proposal]:
        return (
            self.db.query(Proposal)
            .filter(
                Proposal.job_id == job_id,
                Proposal.id != exclude_proposal_id,
                Proposal.status == ProposalStatus.PENDING,
            )
            .all()
        )

    def update_status(self, proposal: Proposal, proposal_status: ProposalStatus) -> Proposal:
        proposal.status = proposal_status
        self.db.commit()
        self.db.refresh(proposal)
        return proposal

    def _paginate(self, query, page: int, page_size: int):
        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()
        return items, total

    def list_by_freelancer(self, freelancer_id, *, page: int, page_size: int):
        query = (
            self.db.query(Proposal)
            .filter(Proposal.freelancer_id == freelancer_id)
            .order_by(Proposal.created_at.desc())
        )
        return self._paginate(query, page, page_size)

    def list_by_job(self, job_id, *, page: int, page_size: int):
        query = (
            self.db.query(Proposal)
            .filter(Proposal.job_id == job_id)
            .order_by(Proposal.created_at.desc())
        )
        return self._paginate(query, page, page_size)
