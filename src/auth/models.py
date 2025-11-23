from typing import List
from uuid import UUID
from pydantic import BaseModel
from datetime import date

class RegisterUserRequest(BaseModel) :
    username: str
    password: str
    birthdate: date
    timezone: str

class Token (BaseModel) :
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: str | None = None

    def get_uuid(self) -> UUID | None:
        if self.user_id:
            return UUID(self.user_id)
        return None


class UserPreferenceItem(BaseModel):
    question_id: int
    selected_options: list[str]

class UserPreferencesResponse(BaseModel):
    question_id: int
    selected_options: List[str]

    class Config:
        orm_mode = True
