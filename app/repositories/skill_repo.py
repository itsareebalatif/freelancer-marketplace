from app.models.profile import Skill
from app.repositories.base import BaseRepository


class SkillRepository(BaseRepository):
    def get_by_name(self, name: str) -> Skill | None:
        return self.db.query(Skill).filter(Skill.name == name).first()

    def get_by_id(self, skill_id) -> Skill | None:
        return self.db.query(Skill).filter(Skill.id == skill_id).first()

    def list_all(self) -> list[Skill]:
        return self.db.query(Skill).order_by(Skill.name).all()

    def create(self, *, name: str) -> Skill:
        return self.add(Skill(name=name))
