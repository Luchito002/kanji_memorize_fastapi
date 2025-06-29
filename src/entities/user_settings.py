from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey, String, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID
import uuid

from ..database.core import Base

class UserSettings(Base):
    __tablename__ = "user_settings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False, unique=True)
    theme: Mapped[str] = mapped_column(String, default="system")
    show_kanji_on_home: Mapped[bool] = mapped_column(Boolean, default=True)
    daily_kanji_limit: Mapped[int] = mapped_column(Integer, default=10)
    last_kanji_index: Mapped[int] = mapped_column(Integer, default=0)
