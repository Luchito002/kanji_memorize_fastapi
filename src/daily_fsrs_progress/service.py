from collections import defaultdict
from typing import List
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import desc, func, and_, or_
from sqlalchemy.orm import Session

from src.daily_fsrs_progress.models import AllUsersGroupedJLPTResponse, GroupedJLPTResponse, LearnedKanji, LearnedKnajiResponse, LineProgressResponse, PieChartResponse, UserGroupedJLPT
from src.entities.card import Card
from src.entities.daily_progress import DailyProgress
from src.entities.review_log import ReviewLog
from src.entities.user import User
from src.fsrs.fsrs import Rating
import os
import json


KANJI_FILE = os.path.join(os.path.dirname(__file__), "../kanjis_convertidos_normalizado.json")

try:
    with open(KANJI_FILE, "r", encoding="utf-8") as f:
        _KANJI_DATA = json.load(f)
except FileNotFoundError:
    _KANJI_DATA = []
KANJI_LOOKUP = {entry.get("character"): entry for entry in _KANJI_DATA}



def get_kanji_progress_pie(db: Session, user_id: UUID) -> PieChartResponse:
    # Obtener el último registro de progreso del usuario
    last_progress = (
        db.query(DailyProgress)
        .filter(DailyProgress.user_id == user_id)
        .order_by(desc(DailyProgress.progress_date))
        .first()
    )

    if not last_progress:
        return PieChartResponse(labels=["Aprendidos", "Pendientes"], values=[0, 0])

    # Total de kanji revisados hasta la fecha actual
    total_kanji = last_progress.start_kanji_index + last_progress.today_kanji_index

    learned_kanji = 0
    cards = db.query(Card).filter(Card.user_id == user_id).all()

    for card in cards:
        logs = db.query(ReviewLog).filter(ReviewLog.card_id == card.id).all()
        for log in logs:
            if (
                log.rating in (Rating.Good.value, Rating.Easy.value)
                and (log.write_time_sec is None or log.write_time_sec <= 30)
                and (log.stroke_errors is None or log.stroke_errors <= 2)
            ):
                learned_kanji += 1
                break

    remaining_kanji = max(total_kanji - learned_kanji, 0)

    return PieChartResponse(
        labels=["Aprendidos", "Pendientes"], values=[learned_kanji, remaining_kanji]
    )


def get_daily_progress_line_chart(db: Session, user_id: UUID) -> LineProgressResponse:
    # Obtener timezone del usuario (si no existe, usamos UTC)
    user = db.query(User).filter(User.id == user_id).first()
    user_tz_str: str = getattr(user, "timezone", "UTC") if user else "UTC"

    # Criterios EXACTOS del pie chart
    good_vals = (Rating.Good.value, Rating.Easy.value)
    learned_filter = and_(
        ReviewLog.rating.in_(good_vals),
        or_(ReviewLog.write_time_sec == None, ReviewLog.write_time_sec <= 30),
        or_(ReviewLog.stroke_errors == None, ReviewLog.stroke_errors <= 2),
        ReviewLog.user_id == user_id,
    )

    # Subconsulta: por cada card_id, obtener la primera datetime que cumple los criterios
    first_learned_subq = (
        db.query(
            ReviewLog.card_id.label("card_id"),
            func.min(ReviewLog.review_datetime).label("first_learned_at"),
        )
        .filter(learned_filter)
        .group_by(ReviewLog.card_id)
        .subquery()
    )

    # Unir con Card para asegurarnos de que la card pertenece al usuario (seguridad)
    q = (
        db.query(first_learned_subq.c.first_learned_at)
        .join(Card, Card.id == first_learned_subq.c.card_id)
        .filter(Card.user_id == user_id)
    )

    rows = q.all()  # lista de tuples con (first_learned_at,)

    if not rows:
        return LineProgressResponse(x_axis=[], y_axis=[], max_y=0)

    # Agrupar por fecha local usando la timezone del usuario
    tz = ZoneInfo(user_tz_str or "UTC")
    counts_by_date = defaultdict(int)

    for (dt_utc,) in rows:
        # dt_utc es un datetime con tzinfo (guardado en UTC). Convertir a tz del usuario.
        if dt_utc is None:
            continue
        dt_local = dt_utc.astimezone(tz)
        date_local_iso = dt_local.date().isoformat()
        counts_by_date[date_local_iso] += 1

    # Ordenar fechas y formar arrays
    x_axis = sorted(counts_by_date.keys())
    y_axis = [counts_by_date[d] for d in x_axis]
    max_y = max(y_axis) if y_axis else 0

    return LineProgressResponse(x_axis=x_axis, y_axis=y_axis, max_y=max_y)


def _is_card_learned(db: Session, card_id: int, user_id: UUID) -> bool:
    """
    Misma lógica que en el pie chart:
      - rating in (Good, Easy)
      - write_time_sec is None or <= 30
      - stroke_errors is None or <= 2
      - review belongs to the same user
    Retorna True si existe al menos un ReviewLog que cumpla.
    """
    good_vals = (Rating.Good.value, Rating.Easy.value)

    # Traer logs de esa card hechos por el usuario
    logs: List[ReviewLog] = (
        db.query(ReviewLog)
        .filter(ReviewLog.card_id == card_id, ReviewLog.user_id == user_id)
        .all()
    )

    for log in logs:
        if (
            log.rating in good_vals
            and (log.write_time_sec is None or log.write_time_sec <= 30)
            and (log.stroke_errors is None or log.stroke_errors <= 2)
        ):
            return True
    return False


def get_learned_kanji_grouped_by_jlpt(db: Session, user_id: UUID) -> GroupedJLPTResponse:
    groups = {
        "n1": [],
        "n2": [],
        "n3": [],
        "n4": [],
        "n5": [],
    }

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return GroupedJLPTResponse(
            learned_count=0,
            n1=[],
            n2=[],
            n3=[],
            n4=[],
            n5=[]
        )

    cards: List[Card] = db.query(Card).filter(Card.user_id == user_id).all()

    learned_count = 0

    for card in cards:
        # Determinar si la card está aprendida (misma regla que en pie)
        if _is_card_learned(db, card.id, user_id):
            learned_count += 1
            kanji_char = card.kanji_char

            kanji_info = KANJI_LOOKUP.get(kanji_char)

            if kanji_info:
                jlpt_raw = kanji_info.get("jlpt") or ""
                jlpt_key = (jlpt_raw or "").lower()  # esperar cosas como "N5", "n3", etc.
                jlpt_key = jlpt_key if jlpt_key in groups else None

                learned = LearnedKanji(
                    character=kanji_info.get("character", kanji_char),
                    meaning=kanji_info.get("meaning"),
                    jlpt=(jlpt_raw.lower() if isinstance(jlpt_raw, str) else jlpt_raw)
                )

                if jlpt_key:
                    groups[jlpt_key].append(learned)
                else:
                    pass
            else:
                learned = LearnedKanji(
                    character=kanji_char,
                    meaning=None,
                    jlpt=None
                )
                pass

    return GroupedJLPTResponse(
        learned_count=learned_count,
        n1=groups["n1"],
        n2=groups["n2"],
        n3=groups["n3"],
        n4=groups["n4"],
        n5=groups["n5"]

    )

def get_all_users_learned_kanji_grouped_by_jlpt(db: Session) -> AllUsersGroupedJLPTResponse:
    # Obtener todos los usuarios normales
    users: List[User] = db.query(User).filter(User.rol == "user").all()

    results = []

    for user in users:
        # Reusar tu lógica individual
        grouped = get_learned_kanji_grouped_by_jlpt(db, user.id)

        result_item = UserGroupedJLPT(
            user_id=user.id,
            username=user.username,
            data=grouped
        )

        results.append(result_item)

    return AllUsersGroupedJLPTResponse(results=results)


def get_learned_kanji_count(db: Session, user_id: UUID) -> LearnedKnajiResponse:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return LearnedKnajiResponse(count=0)

    cards: List[Card] = db.query(Card).filter(Card.user_id == user_id).all()

    learned_count = 0
    for card in cards:
        if _is_card_learned(db, card.id, user_id):
            learned_count += 1

    return LearnedKnajiResponse(count=learned_count)
