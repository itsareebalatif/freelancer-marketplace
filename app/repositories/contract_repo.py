from sqlalchemy import or_

from app.models.contract import Contract
from app.repositories.base import BaseRepository


class ContractRepository(BaseRepository):
    def get_by_id(self, contract_id) -> Contract | None:
        return self.db.query(Contract).filter(Contract.id == contract_id).first()

    def get_by_proposal_id(self, proposal_id) -> Contract | None:
        return self.db.query(Contract).filter(Contract.proposal_id == proposal_id).first()

    def update(self, contract: Contract, **fields) -> Contract:
        for key, value in fields.items():
            setattr(contract, key, value)
        self.db.commit()
        self.db.refresh(contract)
        return contract

    def list_for_user(self, user_id, *, page: int, page_size: int):
        query = (
            self.db.query(Contract)
            .filter(or_(Contract.client_id == user_id, Contract.freelancer_id == user_id))
            .order_by(Contract.created_at.desc())
        )
        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()
        return items, total
