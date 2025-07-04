from typing import Annotated
from fastapi import APIRouter, Depends, Request
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
