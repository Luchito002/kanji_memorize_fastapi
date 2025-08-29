from typing import List
from fastapi import APIRouter, HTTPException

from src.api_response import APIResponse
from src.auth.service import CurrentUser
from src.database.core import DbSession
from src.srs.models import KanjiSRSResponse
from . import service

router = APIRouter(
    prefix="/srs",
    tags=["srs"]
)

@router.get("/due-kanji", response_model=APIResponse[List[KanjiSRSResponse]])
def get_due_kanji(current_user: CurrentUser, db: DbSession):
    user_id = current_user.get_uuid()
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token or user not found")

    data = service.get_due_kanji(db, user_id)
    if data is None:
        raise HTTPException(status_code=404, detail="User settings not found")

    return APIResponse(
        result=data,
        status="success",
        message="Settings loaded successfully"
    )
