from uuid import UUID

from sqlalchemy import desc
from sqlalchemy.orm import Session

from src.daily_fsrs_progress.models import LineProgressResponse, PieChartResponse
from src.entities.card import Card
from src.entities.daily_progress import DailyProgress
from src.entities.review_log import ReviewLog
from src.entities.daily_fsrs_progress import DailyFSRSProgress
from src.fsrs.fsrs import Rating

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
    # Traer todas las entradas de progreso diario
    daily_progress = (
        db.query(DailyFSRSProgress)
        .filter(DailyFSRSProgress.user_id == user_id)
        .order_by(DailyFSRSProgress.progress_date)
        .all()
    )

    x_axis = []
    y_axis = []
    max_y = 0

    for day in daily_progress:
        x_axis.append(day.progress_date.isoformat())
        reviewed_count = len(day.reviewed_cards)  # <-- contar realmente las revisadas
        y_axis.append(reviewed_count)
        if reviewed_count > max_y:
            max_y = reviewed_count

    return LineProgressResponse(x_axis=x_axis, y_axis=y_axis, max_y=max_y)
