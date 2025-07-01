from uuid import UUID
from sqlalchemy.orm import Session
from src.entities.daily_progress import DailyProgress
from src.entities.user_settings import UserSettings
from src.exceptions import DailyProgressNotFound
from .models import DailyProgressResponse
from datetime import date
import logging

def post_increase_today_kanji_index(db: Session, user_id: UUID):
    # Get today's daily progress entry
    user_daily_progress = db.query(DailyProgress).filter(
        DailyProgress.user_id == user_id,
        DailyProgress.progress_date == date.today()
    ).first()

    if not user_daily_progress:
        logging.warning(f"Daily progress not found for user ID: {user_id}")
        raise DailyProgressNotFound()

    # Increase the index of kanji learned today
    user_daily_progress.today_kanji_index += 1
    db.commit()
    db.refresh(user_daily_progress)

    logging.info(f"Incremented today_kanji_index for user ID: {user_id}")

    return user_daily_progress.last_kanji_index



def post_decrease_today_kanji_index(db: Session, user_id: UUID):
    # Get today's daily progress entry
    user_daily_progress = db.query(DailyProgress).filter(
        DailyProgress.user_id == user_id,
        DailyProgress.progress_date == date.today()
    ).first()

    if not user_daily_progress:
        logging.warning(f"Daily progress not found for user ID: {user_id}")
        raise DailyProgressNotFound()

    # Decrease the index of kanji learned today
    user_daily_progress.today_kanji_index -= 1
    db.commit()
    db.refresh(user_daily_progress)

    logging.info(f"Incremented today_kanji_index for user ID: {user_id}")

    return user_daily_progress.last_kanji_index


def post_complete_daily_progress(db: Session, user_id: UUID):
    # Get today's daily progress entry
    user_daily_progress = db.query(DailyProgress).filter(
        DailyProgress.user_id == user_id,
        DailyProgress.progress_date == date.today()
    ).first()

    if not user_daily_progress:
        logging.warning(f"Daily progress not found for user ID: {user_id}")
        raise DailyProgressNotFound()

    # Complete the daily progress
    user_daily_progress.completed = True
    db.commit()
    db.refresh(user_daily_progress)

    logging.info(f"Completed daily progress for user ID: {user_id}")

    return user_daily_progress.completed



def post_create_today_progress(db: Session, user_id: UUID) -> DailyProgressResponse:
    today = date.today()

    # Try to get today's progress
    progress = db.query(DailyProgress).filter_by(user_id=user_id, progress_date=today).first()

    # Get daily limit from user settings
    settings = db.query(UserSettings).filter_by(user_id=user_id).first()
    if not settings:
        raise Exception("User settings not found")

    if not progress:
        # Get last progress to determine new base index
        last = (
            db.query(DailyProgress)
            .filter_by(user_id=user_id)
            .order_by(DailyProgress.progress_date.desc())
            .first()
        )

        last_index = (last.last_kanji_index + last.today_kanji_index) if last else 0

        # Create today's new progress
        progress = DailyProgress(
            user_id=user_id,
            progress_date=today,
            last_kanji_index=last_index,
            today_kanji_index=last_index + 1,
        )
        db.add(progress)
        db.commit()
        db.refresh(progress)

    return DailyProgressResponse(
        last_kanji_index=progress.last_kanji_index,
        today_kanji_index=progress.today_kanji_index,
        end_kanji_index=progress.last_kanji_index + settings.daily_kanji_limit,
        completed=progress.completed
    )
