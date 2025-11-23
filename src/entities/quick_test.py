from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy import ForeignKey, Integer, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid
from ..database.core import Base


class QuickTest(Base):
    __tablename__ = "quick_tests"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    limit: Mapped[int] = mapped_column(Integer, nullable=False)
    current: Mapped[int] = mapped_column(Integer, default=0)
    correct_count: Mapped[int] = mapped_column(Integer, default=0)
    wrong_count: Mapped[int] = mapped_column(Integer, default=0)

    state: Mapped[str] = mapped_column(String, default="in_progress")
    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relaciones
    user = relationship("User", back_populates="quick_tests")
    questions: Mapped[list["QuickTestQuestion"]] = relationship(
        back_populates="test",
        cascade="all, delete-orphan",
        order_by="QuickTestQuestion.order",
    )
