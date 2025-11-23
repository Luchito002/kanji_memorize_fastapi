from typing import List, Optional
from pydantic import BaseModel

class UserGenerateStoryResponse(BaseModel) :
    story: str

class UserGetStoryResponse(BaseModel) :
    story: str

class Radical(BaseModel):
    char: str
    meaning: str

class UserGenerateStoryRequest(BaseModel):
    kanji_meaning: Optional[str]
    kanji_char: Optional[str]
    radicals: Optional[List[Radical]]

class UserGetStoryRequest(BaseModel):
    kanji_char: Optional[str]
