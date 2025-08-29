from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Text, Integer
from ..database.core import Base

class UserPreferencesQuestions(Base):
    __tablename__ = "user_preferences_questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    max_selection: Mapped[int] = mapped_column(Integer, nullable=False)

    user_preferences = relationship("UserPreferences", back_populates="question")
