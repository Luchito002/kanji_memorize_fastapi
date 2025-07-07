from fastapi import APIRouter, HTTPException
from src.api_response import APIResponse
from src.database.core import DbSession
from src.kanjidraw import service
from .models import MatchRequest, MatchResponse, StrokeInput, StrokeValidationResult
from ..auth.service import CurrentUser

router = APIRouter(
    prefix="/kanjimatch",
    tags=["kanjimatch"]
)

@router.post("/match", response_model=APIResponse[MatchResponse])
def get_current_user_settings(current_user: CurrentUser, db: DbSession, body: MatchRequest):
    user_id = current_user.get_uuid()
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token")

    result = service.match_kanji(body.strokes)
    return APIResponse(
        result=result,
        status="success",
        message="Top kanji matches"
    )


@router.post("/validate-stroke", response_model=APIResponse[StrokeValidationResult])
def validate_stroke(current_user: CurrentUser, db: DbSession, body: StrokeInput):
    user_id = current_user.get_uuid()
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token")

    result = service.validate_stroke_logic(body)

    return APIResponse(
        result=result,
        status="success",
        message="Top kanji matches"
    )
