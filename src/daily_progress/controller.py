from fastapi import APIRouter, HTTPException
from src.api_response import APIResponse
from src.database.core import DbSession
from . import service
from ..auth.service import CurrentUser
from .models import IncreaseEndKanjiIndexRequest, Kanji, KanjiCharRequest

router = APIRouter(
    prefix="/dailyprogress",
    tags=["dailyprogress"]
)

@router.post("/increase-daily-progress", response_model=APIResponse)
def post_increase_daily_progress(payload: KanjiCharRequest, current_user: CurrentUser, db: DbSession):
    user_id = current_user.get_uuid()
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token or user not found")

    new_index = service.post_increase_today_kanji_index(db, user_id, payload.kanji_char)

    return APIResponse(
        result=new_index,
        status="success",
        message="last_kanji_index updated successfully"
    )

@router.post("/decrease-daily-progress", response_model=APIResponse)
def post_decrease_daily_progress(payload: KanjiCharRequest, current_user: CurrentUser, db: DbSession):
    user_id = current_user.get_uuid()
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token or user not found")

    new_index = service.post_decrease_today_kanji_index(db, user_id, payload.kanji_char)

    return APIResponse(
        result=new_index,
        status="success",
        message="last_kanji_index updated successfully"
    )

@router.post("/complete-daily-progress", response_model=APIResponse)
def post_complete_daily_progress(current_user: CurrentUser, db: DbSession):
    user_id = current_user.get_uuid()
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token or user not found")

    completed = service.post_complete_daily_progress(db, user_id)

    return APIResponse(
        result=completed,
        status="success",
        message="Daily progress completed successfully"
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

@router.put("/increase-end-kanji-index", response_model=APIResponse)
def put_increase_end_kanji_index(current_user: CurrentUser, db: DbSession, payload: IncreaseEndKanjiIndexRequest):
    user_id = current_user.get_uuid()
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token or user not found")

    result = service.put_increase_end_kanji_index(db, user_id, payload.increment)

    return APIResponse(
        result=result,
        status="success",
        message="request completed successfully"
    )

@router.get("/get-last-kanji-viewed", response_model=APIResponse[Kanji])
def get_last_kanji_viewed(current_user:CurrentUser, db:DbSession):
    user_id = current_user.get_uuid()
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token or user not found")

    result = service.get_last_kanji_viewed(db, user_id)

    return APIResponse(
        result=result,
        status="success",
        message="request completed successfully"
    )

