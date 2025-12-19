from fastapi import APIRouter, HTTPException

from src.api_response import APIResponse
from src.database.core import DbSession

from . import models, service
from ..auth.service import CurrentUser

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

@router.get("/me", response_model=models.UserResponse)
def get_current_user(current_user: CurrentUser, db: DbSession):
    user_id = current_user.get_uuid()
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token or user not found")
    return service.get_user_by_id(db, user_id)

@router.put("/edit-user", response_model=APIResponse[models.UserResponse])
def put_edit_user(current_user: CurrentUser, db: DbSession, newUser: models.UserEditRequest):
    user_id = current_user.get_uuid()
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token or user not found")

    result = service.put_edit_user(db, user_id, newUser)

    return APIResponse(
        result=result,
        status="success",
        message="User edited successfully"
    )

@router.get("/all-users", response_model=APIResponse[models.UserListResponse])
def get_all_normal_users(current_user: CurrentUser, db: DbSession):
    user_id = current_user.get_uuid()
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token or user not found")

    result = service.get_all_normal_users(db, user_id)

    return APIResponse(
        result=result,
        status="success",
        message="Users retrieved successfully"
    )
