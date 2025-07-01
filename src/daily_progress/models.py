from pydantic import BaseModel

class DailyProgressResponse(BaseModel):
    last_kanji_index: int
    today_kanji_index: int
    end_kanji_index: int
    completed: bool
