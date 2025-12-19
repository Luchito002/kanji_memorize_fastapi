from fastapi import APIRouter, HTTPException

from src.api_response import APIResponse
from src.auth.service import CurrentUser
from src.daily_fsrs_progress.models import AllUsersGroupedJLPTResponse, GroupedJLPTResponse, LearnedKanjiRequest, LearnedKnajiResponse, LineProgressResponse, PieChartResponse
from src.database.core import DbSession

from . import service

router = APIRouter(
    prefix="/dailyfsrsprogress",
    tags=["dailyfsrsprogress"]
)

@router.get("/piechart", response_model=APIResponse[PieChartResponse])
def get_kanji_progress_pie(current_user: CurrentUser, db: DbSession):
    user_id = current_user.get_uuid()
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token or user not found")

    card = service.get_kanji_progress_pie(db, user_id)
    return APIResponse(result=card, status="success", message="Pie chart success")


@router.get("/progressline", response_model=APIResponse[LineProgressResponse])
def get_daily_progress_line_chart(current_user: CurrentUser, db: DbSession):
    user_id = current_user.get_uuid()
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token or user not found")

    card = service.get_daily_progress_line_chart(db, user_id)
    return APIResponse(result=card, status="success", message="Line chart success")


@router.post("/learned-kanji-jlpt", response_model=GroupedJLPTResponse)
def get_learned_kanji_by_jlpt(request: LearnedKanjiRequest, db: DbSession):
    user_id = request.user_id
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token or user not found")

    result = service.get_learned_kanji_grouped_by_jlpt(db, user_id)
    return result


@router.get("/learned-kanji-all-users", response_model=APIResponse[AllUsersGroupedJLPTResponse])
def get_all_users_learned_kanji_grouped_by_jlpt(current_user: CurrentUser, db: DbSession):
    user_id = current_user.user_id
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token or user not found")

    result = service.get_all_users_learned_kanji_grouped_by_jlpt(db)

    return APIResponse(result=result, status="success", message="All data got")


@router.post("/learned-kanji-count", response_model=LearnedKnajiResponse)
def get_learned_kanji_count(request: LearnedKanjiRequest, db: DbSession):
    user_id = request.user_id
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token or user not found")

    result = service.get_learned_kanji_count(db, user_id)
    return result
