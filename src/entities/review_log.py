from sqlalchemy import DateTime, ForeignKey, Float, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timezone
import uuid
from ..database.core import Base

class ReviewLog(Base):
    __tablename__ = "review_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    card_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cards.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"),nullable=False)

    rating: Mapped[int] = mapped_column(Integer,nullable=False)
    review_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    review_duration: Mapped[float] = mapped_column(Float, nullable=True)

    write_time_sec: Mapped[float] = mapped_column(Float, nullable=True)
    stroke_errors: Mapped[int] = mapped_column(Integer, nullable=True)

    card = relationship("Card", back_populates="reviews")
    user = relationship("User")
