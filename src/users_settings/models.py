from typing import Optional
from pydantic import BaseModel

class UserSettingsResponse(BaseModel) :
    theme: str
    daily_kanji_limit: int
    daily_srs_limit:int


class UserEditSettingsRequest(BaseModel):
    theme: Optional[str]
    daily_kanji_limit: Optional[int]
    daily_srs_limit:Optional[int]
