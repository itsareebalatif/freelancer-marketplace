from app.models.contract import Milestone
from app.repositories.base import BaseRepository


class MilestoneRepository(BaseRepository):
    def get_by_id(self, milestone_id) -> Milestone | None:
        return self.db.query(Milestone).filter(Milestone.id == milestone_id).first()

    def list_by_contract(self, contract_id) -> list[Milestone]:
        return (
            self.db.query(Milestone)
            .filter(Milestone.contract_id == contract_id)
            .order_by(Milestone.created_at.asc())
            .all()
        )

    def create(self, *, contract_id, **fields) -> Milestone:
        return self.add(Milestone(contract_id=contract_id, **fields))

    def update_status(self, milestone: Milestone, milestone_status) -> Milestone:
        milestone.status = milestone_status
        self.db.commit()
        self.db.refresh(milestone)
        return milestone
