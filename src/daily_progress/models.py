from pydantic import BaseModel

class DailyProgressResponse(BaseModel):
    start_kanji_index: int
    end_kanji_index: int
    today_kanji_index: int
    completed: bool

class IncreaseEndKanjiIndexRequest(BaseModel):
    increment: int
