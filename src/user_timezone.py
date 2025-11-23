from datetime import datetime, timezone
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from src.entities.user import User


def to_user_timezone(dt: datetime, tz_str: str) -> datetime:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)  # asumir UTC si es naive
    return dt.astimezone(ZoneInfo(tz_str))


def get_user_timezone(db: Session, user_id: UUID) -> str:
    user = db.query(User).filter(User.id == user_id).first()
    return user.timezone if user and user.timezone else "UTC"
