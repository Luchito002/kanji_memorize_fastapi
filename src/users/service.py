from uuid import UUID
from sqlalchemy.orm import Session
from .models import UserResponse, UserEditRequest
from src.entities.user import User
from src.exceptions import UserNotFoundError
import logging

def get_user_by_id(db: Session, user_id: UUID) -> UserResponse:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        logging.warning(f"User not found with ID: {user_id}")
        raise UserNotFoundError(user_id)
    logging.info(f"Successfully retrieved user with ID: {user_id}")
    return user

def put_edit_user(db: Session, user_id: UUID, newUser:UserEditRequest) -> UserResponse:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        logging.warning(f"User not found with ID: {user_id}")
        raise UserNotFoundError(user_id)
    logging.info(f"Successfully retrieved user with ID: {user_id}")

    if newUser.username is not None:
        user.username = newUser.username
    if newUser.birthdate is not None:
        user.birthdate = newUser.birthdate

    db.commit()
    db.refresh(user)

    return UserResponse(
        username=user.username,
        birthdate=user.birthdate,
        created_at=user.created_at,
    )
