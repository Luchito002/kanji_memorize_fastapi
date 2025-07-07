from pydantic import BaseModel, Field
from typing import List, TypeVar

T = TypeVar("T")

class MatchRequest(BaseModel):
    strokes: List[List[float]] = Field(..., description="List of stroke lines")

class MatchResult(BaseModel):
    kanji: str
    score: int

class MatchResponse(BaseModel):
    matches: List[MatchResult]

class StrokeInput(BaseModel):
    kanji: str
    stroke_index: int
    user_line: List[float]  # [x1, y1, x2, y2]

class StrokeValidationResult(BaseModel):
    ok: bool
    message: str
    corrected: List[List[int]]
    done: bool
