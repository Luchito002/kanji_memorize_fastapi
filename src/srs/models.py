from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from src.entities.srs import SRSStatus

class KanjiSRSResponse(BaseModel):
    kanji_char: str
    status: SRSStatus
    ease_factor: float
    interval: int
    repetition: int
    next_review_at: Optional[datetime]
