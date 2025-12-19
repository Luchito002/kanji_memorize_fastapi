from typing import Dict, List, Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel


class CardCreateRequest(BaseModel):
    kanji_char: str


class CardResponse(BaseModel):
    id: int
    user_id: UUID
    kanji_char: str
    state: int
    step: Optional[int] = None
    stability: Optional[float] = None
    difficulty: Optional[float] = None
    due: Optional[datetime] = None
    last_review: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ReviewLogResponse(BaseModel):
    id: UUID
    card_id: int
    user_id: UUID
    rating: int
    review_datetime: datetime
    review_duration: Optional[float]
    write_time_sec: Optional[float]
    stroke_errors: Optional[int]

    class Config:
        orm_mode = True

class TodayCardsResponse(BaseModel):
    todays_cards: List[CardResponse]
    reviewed_cards: List[CardResponse]
    kanji_count: int
    reviewed_count: int
    completed: bool


class ReviewCardRequest(BaseModel):
    card_id: int
    rating: int  # 1: Again, 2: Hard, 3: Good, 4: Easy
    write_time_sec: float
    stroke_errors: int

class ReviewCardResponse(BaseModel):
    card: CardResponse
    review_log: ReviewLogResponse

class ReviewLogsRequest(BaseModel):
    card_id: UUID

class CardWithIntervalsResponse(BaseModel):
    again: str
    hard: str
    good: str
    easy: str

class CardWithIntervalsRequest(BaseModel):
    card_id: int

class CardTodayResponse(BaseModel):
    id: UUID
    user_id: UUID
    kanji_char: str
    fsrs_state: Dict
    created_at: datetime

    class Config:
        orm_mode = True

class IncrementKanjiCountRequest(BaseModel):
    increment:int
