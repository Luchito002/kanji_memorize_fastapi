from pydantic import BaseModel

class UserSettingsResponse(BaseModel) :
    theme: str
    daily_kanji_limit: int
