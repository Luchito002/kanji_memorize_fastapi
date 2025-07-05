from uuid import UUID
from sqlalchemy.orm import Session

from src.entities.daily_progress import DailyProgress

from .models import UserEditSettingsRequest, UserSettingsResponse
from src.entities.user_settings import UserSettings
import logging

from src.exceptions import UserSettingsNotFound

from datetime import date

def get_current_user_settings(db: Session, user_id: UUID) -> UserSettingsResponse:
    user_settings = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
    if not user_settings:
        logging.warning(f"Settings not found with user ID: {user_id}")
        raise UserSettingsNotFound()

    logging.info(f"Successfully retrieved user with ID: {user_id}")
    return UserSettingsResponse(
        theme=user_settings.theme,
        daily_kanji_limit=user_settings.daily_kanji_limit,
    )


def post_create_settings(db: Session, user_id: UUID) -> UserSettingsResponse:
    user_settings = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
    if not user_settings:
        logging.info(f"No settings found for user ID {user_id}, creating new one.")
        user_settings = UserSettings(
            user_id=user_id,
            theme="system",
            daily_kanji_limit=10,
        )
        db.add(user_settings)
        db.commit()
        db.refresh(user_settings)
    else:
        logging.info(f"Settings already exist for user ID {user_id}, returning existing settings.")

    return UserSettingsResponse(
        theme=user_settings.theme,
        daily_kanji_limit=user_settings.daily_kanji_limit,
    )

def put_edit_settings(db: Session, user_id: UUID, newSettings:UserEditSettingsRequest) -> UserSettingsResponse:
    user_settings = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
    if not user_settings:
        logging.warning(f"Settings not found with user ID: {user_id}")
        raise UserSettingsNotFound()

    logging.info(f"Successfully retrieved user with ID: {user_id}")

    if newSettings.theme is not None:
        user_settings.theme = newSettings.theme
    if newSettings.daily_kanji_limit is not None:
        user_settings.daily_kanji_limit = newSettings.daily_kanji_limit

        today_progress = db.query(DailyProgress).filter(
            DailyProgress.user_id == user_id,
            DailyProgress.progress_date == date.today()
        ).first()

        if today_progress:
            today_progress.end_kanji_index = today_progress.start_kanji_index + newSettings.daily_kanji_limit
            today_progress.completed = False
            logging.info(f"Updated today_kanji_index to {newSettings.daily_kanji_limit} for user ID: {user_id}")
        else:
            logging.warning(f"No daily_progress record found for today for user ID: {user_id}")


    print(user_settings.theme)
    print(user_settings.daily_kanji_limit)

    db.commit()
    db.refresh(user_settings)

    return UserSettingsResponse(
        theme=user_settings.theme,
        daily_kanji_limit=user_settings.daily_kanji_limit,
    )
