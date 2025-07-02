from fastapi import APIRouter, HTTPException
from src.api_response import APIResponse
from src.database.core import DbSession
from . import models, service
from ..auth.service import CurrentUser

router = APIRouter(
    prefix="/userssettings",
    tags=["userssettings"]
)

@router.get("/me", response_model=APIResponse[models.UserSettingsResponse])
def get_current_user_settings(current_user: CurrentUser, db: DbSession):
    user_id = current_user.get_uuid()
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token or user not found")

    data = service.get_current_user_settings(db, user_id)
    if data is None:
        raise HTTPException(status_code=404, detail="User settings not found")

    return APIResponse(
        result=data,
        status="success",
        message="Settings loaded successfully"
    )

@router.post("/create-settings", response_model=APIResponse)
def post_create_settings(current_user: CurrentUser, db: DbSession):
    user_id = current_user.get_uuid()
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token or user not found")

    new_settings = service.post_create_settings(db, user_id)
    if new_settings is None:
        raise HTTPException(status_code=500, detail="Server out of service")

    return APIResponse(
        result=new_settings,
        status="success",
        message="New settings created successfully"
    )
