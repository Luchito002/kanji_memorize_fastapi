from typing import List
from uuid import UUID
from sqlalchemy.orm import Session

from src.entities.user_preferences import UserPreferences

from .models import UserPreferencesResponse
import logging

from src.exceptions import UserSettingsNotFound

def get_user_preferences(db: Session, user_id: UUID) -> List[UserPreferencesResponse]:
    user_settings = db.query(UserPreferences).filter(UserPreferences.user_id == user_id).first()
    if not user_settings:
        logging.warning(f"User without preferences: {user_id}")
        raise UserSettingsNotFound()

    prefs = db.query(UserPreferences).filter(UserPreferences.user_id == user_id).all()

    response = [
        UserPreferencesResponse(
            question_id=str(pref.question_id),
            selected_options=pref.selected_options
        )
        for pref in prefs
    ]

    return response
