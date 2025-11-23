from fastapi import APIRouter, HTTPException
from src.api_response import APIResponse
from src.database.core import DbSession
from . import service
from ..auth.service import CurrentUser

router = APIRouter(
    prefix="/userspreferences",
    tags=["userspreferences"]
)

@router.get("/get-user-preferences", response_model=APIResponse)
def get_user_preferences(current_user: CurrentUser, db:DbSession):
    user_id = current_user.get_uuid()
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token or user not found")

    user_preferences = service.get_user_preferences(db, user_id)

    return APIResponse (
        result=user_preferences,
        status="success",
        message="successfully"
    )
