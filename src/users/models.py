from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel
from datetime import date, datetime


class UserResponse(BaseModel) :
    id: UUID
    username: str
    birthdate: date
    created_at: datetime
    rol: str

class UserListResponse(BaseModel):
    users: List[UserResponse]

class PasswordChange(BaseModel) :
    current_password:str
    new_password:str
    new_password_confirm:str

class UserEditRequest(BaseModel) :
    username: Optional[str]
    birthdate: Optional[date]
