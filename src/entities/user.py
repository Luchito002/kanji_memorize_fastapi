from enum import unique
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, DateTime, Date
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, date
import uuid

from ..database.core import Base

class User(Base):
    __tablename__ = 'users'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    #email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    birthdate: Mapped[date] = mapped_column(Date, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    def __repr__(self):
        return f"<User(email='{self.email}', name='{self.name}')>"
