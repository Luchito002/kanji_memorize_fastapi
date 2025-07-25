from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Boolean, ForeignKey, Integer, Date
from uuid import UUID, uuid4
from datetime import date
from ..database.core import Base

class DailyProgress(Base):
    __tablename__ = "daily_progress"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    progress_date: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
    start_kanji_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    end_kanji_index: Mapped[int] = mapped_column(Integer, nullable=False)
    today_kanji_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
