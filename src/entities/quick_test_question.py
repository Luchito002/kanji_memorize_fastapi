from sqlalchemy import ForeignKey, Integer, String, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid
from ..database.core import Base


class QuickTestQuestion(Base):
    __tablename__ = "quick_test_questions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    test_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("quick_tests.id", ondelete="CASCADE"), nullable=False
    )

    kanji_char: Mapped[str] = mapped_column(String, nullable=False)
    correct_meaning: Mapped[str] = mapped_column(String, nullable=False)
    chosen_meaning: Mapped[str | None] = mapped_column(String, nullable=True)

    option_a: Mapped[str | None] = mapped_column(String, nullable=True)
    option_b: Mapped[str | None] = mapped_column(String, nullable=True)
    option_c: Mapped[str | None] = mapped_column(String, nullable=True)
    option_d: Mapped[str | None] = mapped_column(String, nullable=True)

    is_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    order: Mapped[int] = mapped_column(Integer, nullable=False)

    test = relationship("QuickTest", back_populates="questions")
