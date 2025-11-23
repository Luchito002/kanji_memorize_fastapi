from typing import List, Optional
from pydantic import BaseModel

class DailyProgressResponse(BaseModel):
    start_kanji_index: int
    end_kanji_index: int
    today_kanji_index: int
    completed: bool

class IncreaseEndKanjiIndexRequest(BaseModel):
    increment: int

class KanjiCharRequest(BaseModel):
    kanji_char: str

class Radical(BaseModel):
    char: str
    meaning: str

class Kanji(BaseModel):
    position: int
    character: str
    radicals: List[Radical]
    meaning: str
    story: str
    jlpt: str
    strokeOrder: str
    easyRemember: str
    examples: Optional[List[str]] = None
    kanjiEasyRemember: Optional[str] = None
    radicalExplanation: Optional[str] = None
    radicalExplanationMeanings: Optional[List[Radical]] = None
