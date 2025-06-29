from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey, Text, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from ..database.core import Base

class UserStory(Base):
    __tablename__ = "user_stories"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    kanji_char: Mapped[str] = mapped_column(String(1), nullable=False)  # Ej: "日"
    story: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)
