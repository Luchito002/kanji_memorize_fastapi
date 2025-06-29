from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey, String, Float, Integer, DateTime
from datetime import datetime
from ..database.core import Base

class Progress(Base):
    __tablename__ = "progress"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    kanji_char: Mapped[str] = mapped_column(String(1), primary_key=True)  # Ej. "日"

    status: Mapped[str] = mapped_column(String, nullable=False)  # 'learning', 'learned', etc.
    ease_factor: Mapped[float] = mapped_column(Float, default=2.5)
    interval: Mapped[int] = mapped_column(Integer, default=1)
    repetition: Mapped[int] = mapped_column(Integer, default=0)
    last_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    next_review_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
