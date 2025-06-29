from fastapi import APIRouter, HTTPException

from src.database.core import DbSession

from . import models, service
from ..auth.service import CurrentUser

router = APIRouter(
    prefix="/userssettings",
    tags=["userssettings"]
)

@router.get("/me", response_model=models.UserSettingsByUserIdResponse)
def get_current_user(current_user: CurrentUser, db: DbSession):
    user_id = current_user.get_uuid()
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token or user not found")
    return service.get_user_settings_by_user_id(db, user_id)
