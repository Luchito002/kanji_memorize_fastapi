from typing import Optional
from pydantic import BaseModel
from datetime import date, datetime

class UserResponse(BaseModel) :
    username: str
    birthdate: date
    created_at: datetime

class PasswordChange(BaseModel) :
    current_password:str
    new_password:str
    new_password_confirm:str

class UserEditRequest(BaseModel) :
    username: Optional[str]
    birthdate: Optional[date]
