from datetime import datetime, timezone
from sqlalchemy import DateTime, func
from sqlalchmey.orm import Mapped, mapped_column,DeclarativeBase

class Base(DeclarativeBase):
    pass

class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

