from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository):
    def get_by_email(self, email: str) -> User | None:
        return self.db.query(User).filter(User.email == email).first()

    def get_by_id(self, user_id) -> User | None:
        return self.db.query(User).filter(User.id == user_id).first()

    def create(self, *, email: str, hashed_password: str, role, full_name: str | None = None) -> User:
        user = User(email=email, full_name=full_name, hashed_password=hashed_password, role=role)
        return self.add(user)
