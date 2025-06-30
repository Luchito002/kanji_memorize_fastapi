from fastapi import APIRouter, HTTPException
from src.api_response import APIResponse
from src.database.core import DbSession
from . import models, service
from ..auth.service import CurrentUser

router = APIRouter(
    prefix="/userssettings",
    tags=["userssettings"]
)

@router.get("/me", response_model=APIResponse[models.GetUserSettingsResponse])
def get_current_user(current_user: CurrentUser, db: DbSession):
    user_id = current_user.get_uuid()
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token or user not found")

    data = service.get_user_settings_by_user_id(db, user_id)
    if data is None:
        raise HTTPException(status_code=404, detail="User settings not found")

    return APIResponse(
        result=data,
        status="success",
        message="Configuración cargada correctamente"
    )

@router.post("/lastkanjiindex", response_model=APIResponse)
def post_last_kanji_index(current_user: CurrentUser, db: DbSession):
    user_id = current_user.get_uuid()
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token or user not found")

    new_index = service.post_last_kanji_index(db, user_id)

    return APIResponse(
        result=new_index,
        status="success",
        message="last_kanji_index actualizado correctamente"
    )
