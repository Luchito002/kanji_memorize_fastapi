from fastapi import APIRouter, HTTPException


from . import models, service
from src.database.core import DbSession
from src.api_response import APIResponse
from src.auth.service import CurrentUser

router = APIRouter(prefix="/fsrs", tags=["FSRS"])


@router.post("/create-card", response_model=APIResponse[models.CardResponse])
def post_create_card(
    request: models.CardCreateRequest, current_user: CurrentUser, db: DbSession
):
    user_id = current_user.get_uuid()
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token or user not found")

    card = service.create_card(db, user_id, request.kanji_char)
    return APIResponse(
        result=card, status="success", message="Card created successfully"
    )


@router.post("/get-intervals", response_model=APIResponse[models.CardWithIntervalsResponse])
def get_card_intervals(
    current_user: CurrentUser, db: DbSession, request: models.CardWithIntervalsRequest
):
    user_id = current_user.get_uuid()
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token or user not found")

    result = service.get_card_intervals(db, request.card_id, user_id)
    return APIResponse(result=result)


@router.post("/review-card", response_model=APIResponse)
def post_review_card(
    current_user: CurrentUser, db: DbSession, request: models.ReviewCardRequest
):
    user_id = current_user.get_uuid()
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token or user not found")

    result = service.post_review_card(db, user_id, request)
    return APIResponse(result=result)


@router.get("/get-today-cards", response_model=APIResponse[models.TodayCardsResponse])
def get_today_cards(current_user: CurrentUser, db: DbSession):
    user_id = current_user.get_uuid()
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token or user not found")

    result = service.get_today_cards(db, user_id)
    return APIResponse(result=result)


@router.post("/increment-kanji-count", response_model=APIResponse[models.TodayCardsResponse])
def increment_kanji_count(current_user: CurrentUser, db: DbSession, request: models.IncrementKanjiCountRequest):
    user_id = current_user.get_uuid()
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token or user not found")

    result = service.increase_daily_kanji(db, user_id, request.increment)
    return APIResponse(result=result)
