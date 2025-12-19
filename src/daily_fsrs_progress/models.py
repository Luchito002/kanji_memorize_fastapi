from uuid import UUID
from pydantic import BaseModel
from typing import List, Optional

class PieChartResponse(BaseModel):
    labels: List[str]
    values: List[int]

class DailyProgressPoint(BaseModel):
    date: str
    learned_kanji: int

class LineProgressResponse(BaseModel):
    x_axis: List[str]
    y_axis: List[int]
    max_y: int

class LearnedKanji(BaseModel):
    character: str
    meaning: Optional[str]
    jlpt: Optional[str]

class GroupedJLPTResponse(BaseModel):
    learned_count: int
    n1: List[LearnedKanji]
    n2: List[LearnedKanji]
    n3: List[LearnedKanji]
    n4: List[LearnedKanji]
    n5: List[LearnedKanji]

class LearnedKanjiRequest (BaseModel) :
    user_id: UUID

class LearnedKnajiResponse (BaseModel) :
    count: int

class UserGroupedJLPT(BaseModel):
    user_id: UUID
    username: str
    data: GroupedJLPTResponse

class AllUsersGroupedJLPTResponse(BaseModel):
    results: List[UserGroupedJLPT]
