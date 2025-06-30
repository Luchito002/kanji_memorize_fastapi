from uuid import UUID
from sqlalchemy.orm import Session

from src.exceptions import UserSettingsNotFound
from . import models
from src.entities.user_settings import UserSettings
import logging

def get_user_settings_by_user_id(db: Session, user_id: UUID) -> models.GetUserSettingsResponse:
    user_settings = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
    if not user_settings:
        logging.warning(f"Settings not found with user ID: {user_id}")

    logging.info(f"Successfully retrieved user with ID: {user_id}")
    return user_settings


def post_last_kanji_index(db: Session, user_id: UUID):
    user_settings = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
    if not user_settings:
        logging.warning(f"Settings not found with user ID: {user_id}")

    if user_settings is None:
        raise UserSettingsNotFound()

    user_settings.last_kanji_index += 1
    db.commit()
    db.refresh(user_settings)
    logging.info(f"Successfully retrieved user with ID: {user_id}")
    return user_settings.last_kanji_index
