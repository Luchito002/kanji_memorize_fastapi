from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import List
from uuid import UUID
from src.entities.srs import SRS, SRSStatus
from src.entities.user_settings import UserSettings
from src.srs.models import KanjiSRSResponse  # ajusta el import según tu proyecto

def get_due_kanji(db: Session, user_id: UUID) -> List[KanjiSRSResponse]:
    now = datetime.now(timezone.utc)

    user_settings = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
    daily_limit = user_settings.daily_srs_limit if user_settings and user_settings.daily_srs_limit else 10

    entries = db.query(SRS).filter(
        SRS.user_id == user_id,
        SRS.status.in_([SRSStatus.learning, SRSStatus.review, SRSStatus.relearning]),
        (
            (SRS.next_review_at == None) |  # No assigned review date yet (new)
            (SRS.next_review_at <= now)     # Review is due
        )
    ).order_by(
        SRS.next_review_at.asc().nullsfirst(),  # New kanji come first
        SRS.status.desc(),  # Prioritize review/relearning, over learning
    ).limit(daily_limit).all()

    return [
        KanjiSRSResponse(
            kanji_char=e.kanji_char,
            status=e.status,
            ease_factor=e.ease_factor,
            interval=e.interval,
            repetition=e.repetition,
            next_review_at=e.next_review_at,
        ) for e in entries
    ]
