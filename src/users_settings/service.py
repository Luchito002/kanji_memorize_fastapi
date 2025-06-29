from uuid import UUID
from sqlalchemy.orm import Session
from . import models
from src.entities.user_settings import UserSettings
import logging

def get_user_settings_by_user_id(db: Session, user_id: UUID) -> models.UserSettingsByUserIdResponse:
    user_settings = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
    if not user_settings:
        logging.warning(f"Settings not found with user ID: {user_id}")

    logging.info(f"Successfully retrieved user with ID: {user_id}")
    return user_settings
