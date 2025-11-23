from uuid import UUID
from sqlalchemy.orm import Session
from src.entities.daily_progress import DailyProgress
from src.entities.user_settings import UserSettings
from src.exceptions import DailyProgressNotFound
from .models import DailyProgressResponse, Kanji
from datetime import date
import os
import json

KANJI_FILE = os.path.join(os.path.dirname(__file__), "../kanjis_convertidos_normalizado.json")

def post_increase_today_kanji_index(db: Session, user_id: UUID, kanji_char: str):
    progress = db.query(DailyProgress).filter(
        DailyProgress.user_id == user_id,
        DailyProgress.progress_date == date.today()
    ).first()

    if not progress:
        raise DailyProgressNotFound()

    current_kanji = progress.start_kanji_index + progress.today_kanji_index

    if current_kanji < progress.end_kanji_index:
        # Incrementar el índice aunque el kanji ya exista
        progress.today_kanji_index += 1

        db.commit()
        db.refresh(progress)

    return current_kanji + 1


def post_decrease_today_kanji_index(db: Session, user_id: UUID, kanji_char: str):
    progress = db.query(DailyProgress).filter(
        DailyProgress.user_id == user_id,
        DailyProgress.progress_date == date.today()
    ).first()

    if not progress:
        raise DailyProgressNotFound()

    if progress.today_kanji_index > 0:
        # Decrementar el índice
        progress.today_kanji_index -= 1

        db.commit()
        db.refresh(progress)

    return progress.start_kanji_index + progress.today_kanji_index


def post_complete_daily_progress(db: Session, user_id: UUID):
    progress = db.query(DailyProgress).filter(
        DailyProgress.user_id == user_id,
        DailyProgress.progress_date == date.today()
    ).first()

    if not progress:
        raise DailyProgressNotFound()

    current_kanji = progress.start_kanji_index + progress.today_kanji_index

    if current_kanji >= progress.end_kanji_index:
        progress.completed = True
        db.commit()
        db.refresh(progress)

    return progress.completed


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
        yesterday = (
            db.query(DailyProgress)
            .filter_by(user_id=user_id)
            .order_by(DailyProgress.progress_date.desc())
            .first()
        )

        start_index = (yesterday.start_kanji_index + yesterday.today_kanji_index) if yesterday else 0
        end_index = start_index + settings.daily_kanji_limit

        if yesterday and yesterday.completed:
            start_index += 1
        elif yesterday:
            end_index -= 1

        # Create today's new progress
        progress = DailyProgress(
            user_id=user_id,
            progress_date=today,
            start_kanji_index=start_index,
            end_kanji_index=end_index,
            today_kanji_index=0,
        )
        db.add(progress)
        db.commit()
        db.refresh(progress)

    return DailyProgressResponse(
        start_kanji_index=progress.start_kanji_index,
        end_kanji_index=progress.end_kanji_index,
        today_kanji_index=progress.today_kanji_index,
        completed=progress.completed
    )


def put_increase_end_kanji_index(db: Session, user_id: UUID, increment: int) -> DailyProgressResponse:
    today = date.today()

    # Try to get today's progress
    progress = db.query(DailyProgress).filter_by(user_id=user_id, progress_date=today).first()

    if not progress:
        raise DailyProgressNotFound()

    progress.end_kanji_index += increment
    progress.completed = False

    db.commit()
    db.refresh(progress)

    return DailyProgressResponse(
        start_kanji_index=progress.start_kanji_index,
        end_kanji_index=progress.end_kanji_index,
        today_kanji_index=progress.today_kanji_index,
        completed=progress.completed
    )

def _load_kanji_list():
    with open(KANJI_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def _get_kanji_by_position(kanjis: list, position: int) -> dict:
    if not kanjis:
        raise RuntimeError("La lista de kanjis está vacía.")
    k = next((k for k in kanjis if k.get("position") == position), None)
    if k:
        return k
    max_pos = max(k.get("position", 0) for k in kanjis)
    min_pos = min(k.get("position", 1) for k in kanjis)
    position = min(max(position, min_pos), max_pos)
    return next((k for k in kanjis if k.get("position") == position), kanjis[0])

def get_last_kanji_viewed(db: Session, user_id: UUID) -> Kanji:
    # Último registro por fecha (no sólo hoy)
    last_progress = (
        db.query(DailyProgress)
        .filter(DailyProgress.user_id == user_id)
        .order_by(DailyProgress.progress_date.desc())
        .first()
    )

    if not last_progress:
        # Usuario nuevo: retorna "一" (posición 1)
        position = 1
    else:
        # Suma pedida
        position = last_progress.start_kanji_index + last_progress.today_kanji_index
        # Aseguramos mínimo 1
        if position < 1:
            position = 1

    kanjis = _load_kanji_list()
    kanji_dict = _get_kanji_by_position(kanjis, position)

    return Kanji(**kanji_dict)
