from sqlalchemy import func

from app.models.review import Review
from app.repositories.base import BaseRepository


class ReviewRepository(BaseRepository):
    def average_rating_for_user(self, user_id) -> float | None:
        result = self.db.query(func.avg(Review.rating)).filter(Review.reviewee_id == user_id).scalar()
        return round(float(result), 2) if result is not None else None

    def get_by_contract_and_reviewer(self, contract_id, reviewer_id) -> Review | None:
        return (
            self.db.query(Review)
            .filter(Review.contract_id == contract_id, Review.reviewer_id == reviewer_id)
            .first()
        )

    def create(self, *, contract_id, reviewer_id, reviewee_id, **fields) -> Review:
        review = Review(contract_id=contract_id, reviewer_id=reviewer_id, reviewee_id=reviewee_id, **fields)
        return self.add(review)

    def list_by_contract(self, contract_id) -> list[Review]:
        return self.db.query(Review).filter(Review.contract_id == contract_id).all()

    def list_by_reviewee(self, user_id, *, page: int, page_size: int):
        query = (
            self.db.query(Review)
            .filter(Review.reviewee_id == user_id)
            .order_by(Review.created_at.desc())
        )
        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()
        return items, total
