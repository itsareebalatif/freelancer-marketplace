import uuid
from typing import List, Optional
from decimal import Decimal
from sqlalchemy import String, Text, Numeric, Integer, ForeignKey, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)

    profiles: Mapped[List["FreelancerProfile"]] = relationship(secondary="freelancer_skills", back_populates="skills")
    jobs: Mapped[List["Job"]] = relationship(secondary="job_skills", back_populates="skills")


class FreelancerSkill(Base):
    __tablename__ = "freelancer_skills"

    freelancer_profile_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("freelancer_profiles.id", ondelete="CASCADE"), primary_key=True)
    skill_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True)


class FreelancerProfile(Base, TimestampMixin):
    __tablename__ = "freelancer_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    hourly_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    experience_years: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    availability: Mapped[str] = mapped_column(String(50), default="Available", nullable=False)

    user: Mapped["User"] = relationship(back_populates="profile")
    skills: Mapped[List["Skill"]] = relationship(secondary="freelancer_skills", back_populates="profiles")