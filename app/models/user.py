import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Enum, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin
from app.models.enums import UserRole

class User(Base, TimestampMixin):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(String(36), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str]= mapped_column(Enum(UserRole), nullable=False)
    is_active: Mapped[bool]= mapped_column(Boolean, default=True)

    freelancer_profile: Mapped["FreelancerProfile"] = relationship("FreelancerProfile", back_populates="user", uselist=False)
    client_profile: Mapped["ClientProfile"] = relationship("ClientProfile", back_populates="user", uselist=False)   
    jobs: Mapped[List["Job"]] = relationship("Job", back_populates="posted_by")
    proposals: Mapped[List["Proposal"]] = relationship("Proposal", back_populates="user")
    contracts: Mapped[List["Contract"]] = relationship("Contract", back_populates="user")
    reviews: Mapped[List["Review"]] = relationship("Review", back_populates="user")
    

class RefreshToken(Base):
 
    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    token: Mapped[str] = mapped_column(String(512), unique=True, index=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    user: Mapped["User"] = relationship(back_populates="refresh_tokens")    