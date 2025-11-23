from fastapi import APIRouter, HTTPException

from src.api_response import APIResponse
from src.auth.service import CurrentUser
from src.daily_fsrs_progress.models import LineProgressResponse, PieChartResponse
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
