from uuid import UUID
from sqlalchemy.orm import Session
from . import models
from src.entities.user import User
from src.exceptions import UserNotFoundError
import logging

def get_user_by_id(db: Session, user_id: UUID) -> models.UserResponse:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        logging.warning(f"User not found with ID: {user_id}")
        raise UserNotFoundError(user_id)
    logging.info(f"Successfully retrieved user with ID: {user_id}")
    return user
