from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, Date
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone, date
import uuid

from ..database.core import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    # email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    birthdate: Mapped[date] = mapped_column(Date, nullable=False)
    rol: Mapped[str] = mapped_column(String, nullable=False, server_default="user")
    password_hash: Mapped[str] = mapped_column(String, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    timezone: Mapped[str] = mapped_column(String, default="UTC", nullable=False)

    # Relaciones
    settings = relationship("UserSettings", backref="user", uselist=False)
    user_stories = relationship("UserStories", backref="user")
    quick_tests: Mapped[list["QuickTest"]] = relationship(
        "QuickTest",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User(username='{self.username}')>"
