from fastapi import APIRouter, HTTPException
from src.api_response import APIResponse
from src.database.core import DbSession
from . import service
from ..auth.service import CurrentUser

router = APIRouter(
    prefix="/dailyprogress",
    tags=["dailyprogress"]
)

@router.post("/increase-daily-progress", response_model=APIResponse)
def post_increase_daily_progress(current_user: CurrentUser, db: DbSession):
    user_id = current_user.get_uuid()
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token or user not found")

    new_index = service.post_increase_today_kanji_index(db, user_id)

    return APIResponse(
        result=new_index,
        status="success",
        message="last_kanji_index actualizado correctamente"
    )

@router.post("/decrease-daily-progress", response_model=APIResponse)
def post_decrease_daily_progress(current_user: CurrentUser, db: DbSession):
    user_id = current_user.get_uuid()
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token or user not found")

    new_index = service.post_decrease_today_kanji_index(db, user_id)

    return APIResponse(
        result=new_index,
        status="success",
        message="last_kanji_index actualizado correctamente"
    )

@router.post("/create-today-progress", response_model=APIResponse)
def post_create_progress(current_user: CurrentUser, db: DbSession):
    user_id = current_user.get_uuid()
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token or user not found")

    result = service.post_create_today_progress(db, user_id)

    return APIResponse(
        result=result,
        status="success",
        message="request completed successfully"
    )
