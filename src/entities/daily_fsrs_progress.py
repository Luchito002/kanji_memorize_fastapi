from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Boolean, Date, Integer, BigInteger
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.dialects.postgresql import UUID
import uuid
from ..database.core import Base
from sqlalchemy.dialects.postgresql import ARRAY

class DailyFSRSProgress(Base):
    __tablename__ = "daily_fsrs_progress"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    progress_date: Mapped[Date] = mapped_column(Date, nullable=False)
    kanji_count: Mapped[int] = mapped_column(Integer, nullable=False)
    reviewed_count: Mapped[int] = mapped_column(Integer, default=1)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    reviewed_cards: Mapped[list[int]] = mapped_column(
        MutableList.as_mutable(ARRAY(BigInteger)), default=list
    )
    todays_cards: Mapped[list[int]] = mapped_column(
        MutableList.as_mutable(ARRAY(BigInteger)), default=list
    )
