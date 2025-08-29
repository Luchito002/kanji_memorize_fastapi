from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, String, Float, Integer, DateTime
from datetime import datetime

from src.srs.srsstatus import SRSStatus

from ..database.core import Base

class SRS(Base):
    __tablename__ = "srs_progress"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    kanji_char: Mapped[str] = mapped_column(String(1), primary_key=True)

    status: Mapped[SRSStatus] = mapped_column(SQLEnum(SRSStatus), nullable=False)
    ease_factor: Mapped[float] = mapped_column(Float, default=2.5, nullable=False)
    interval: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    repetition: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    lapses: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    last_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    next_review_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    last_grade: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_review_duration: Mapped[int | None] = mapped_column(Integer, nullable=True)  # milisegundos
