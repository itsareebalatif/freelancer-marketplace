from app.models.profile import FreelancerProfile, Skill
from app.repositories.base import BaseRepository


class ProfileRepository(BaseRepository):
    def get_by_user_id(self, user_id) -> FreelancerProfile | None:
        return self.db.query(FreelancerProfile).filter(FreelancerProfile.user_id == user_id).first()

    def create(self, *, user_id, **fields) -> FreelancerProfile:
        profile = FreelancerProfile(user_id=user_id, **fields)
        return self.add(profile)

    def update(self, profile: FreelancerProfile, **fields) -> FreelancerProfile:
        for key, value in fields.items():
            setattr(profile, key, value)
        self.db.commit()
        self.db.refresh(profile)
        return profile

    def set_skills(self, profile: FreelancerProfile, skills: list[Skill]) -> FreelancerProfile:
        profile.skills = skills
        self.db.commit()
        self.db.refresh(profile)
        return profile
