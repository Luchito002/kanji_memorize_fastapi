from pydantic import BaseModel
from typing import List

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
