from pydantic import BaseModel

class UserSettingsByUserIdResponse(BaseModel) :
    theme: str
    show_kanji_on_home: bool
    daily_kanji_limit: int
    last_kanji_index: int
