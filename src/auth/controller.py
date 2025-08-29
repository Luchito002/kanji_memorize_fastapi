from typing import Annotated, List
from fastapi import APIRouter, Depends, Request, HTTPException
from starlette import status

from src.api_response import APIResponse
from . import models
from . import service
from fastapi.security import OAuth2PasswordRequestForm
from ..database.core import DbSession
from ..rate_limiter  import limiter

router = APIRouter(
    prefix='/auth',
    tags=['auth']
)

@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=APIResponse[models.Token])
@limiter.limit("5/hour")
async def register_user(request: Request,db: DbSession,register_user_request: models.RegisterUserRequest):
    token = service.register_user(db, register_user_request)
    return APIResponse(result=token)

@router.post("/login", response_model=models.Token)
async def login_for_access_token(form_data: Annotated [OAuth2PasswordRequestForm, Depends()], db: DbSession) :
    return service.login_for_access_token(form_data, db)

@router.post("/user-preferences", response_model=APIResponse)
def post_user_preferences(
    preferences: list[models.UserPreferenceItem],  # Recibimos lista directamente
    current_user: service.CurrentUser,
    db: DbSession
):
    user_id = current_user.get_uuid()
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token or user not found")

    # Convertimos cada item a dict
    prefs_dicts = [pref.dict() for pref in preferences]

    # Llamamos al service batch
    results = service.create_or_update_user_preferences_batch(db, user_id, prefs_dicts)

    return APIResponse(
        result=results,
        status="success",
        message="User preferences saved successfully"
    )
