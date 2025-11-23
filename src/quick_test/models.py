from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel


class QuickQuestionFull(BaseModel):
    id: UUID
    character: str
    meaning: str
    options: List[str]
    chosen_meaning: Optional[str] = None
    is_correct: Optional[bool] = None


class QuickTestData(BaseModel):
    id: UUID
    state: str
    limit: int
    current: int
    correct_count: int
    wrong_count: int
    questions: List[QuickQuestionFull]


class GetQuickTestRequest(BaseModel):
    create_new: bool

class GetQuickTestResponse(BaseModel):
    test: QuickTestData

class SubmitQuickTestAnswerRequest(BaseModel):
    test_id: UUID
    question_id: UUID
    chosen_option: str
    end_time: datetime | None = None

class SubmitQuickTestAnswerResponse(BaseModel):
    test_id: UUID
    question_id: UUID
    is_correct: bool
    current: int
    total: int
    completed: bool
    correct_count: int
    wrong_count: int
