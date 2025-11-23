from typing import Any, Optional
from uuid import UUID
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from fsrs import Card, Rating, State, Scheduler

from src.entities.daily_fsrs_progress import DailyFSRSProgress
from src.entities.user_settings import UserSettings
from src.fsrs.models import (
    CardResponse,
    CardWithIntervalsResponse,
    TodayCardsResponse,
)
from src.user_timezone import get_user_timezone, to_user_timezone

from ..entities.card import Card as CardDB
from ..entities.review_log import ReviewLog as ReviewLogDB

from copy import deepcopy

def create_card(db: Session, user_id: UUID, kanji_char: str) -> CardDB:
    existing_card = db.query(CardDB).filter(
        CardDB.user_id == user_id, CardDB.kanji_char == kanji_char
    ).first()
    if existing_card:
        raise HTTPException(
            status_code=200,
            detail=f"Card for kanji '{kanji_char}' already exists for this user.",
        )

    fsrs_card = Card()

    user_timezone = get_user_timezone(db, user_id)
    now = to_user_timezone(datetime.now(), user_timezone)
    print("create_card timezone:", now.tzinfo)

    card = CardDB(
        id=fsrs_card.card_id,
        user_id=user_id,
        kanji_char=kanji_char,
        state=fsrs_card.state,
        step=fsrs_card.step,
        stability=fsrs_card.stability,
        difficulty=fsrs_card.difficulty,
        due=fsrs_card.due,
        last_review=fsrs_card.last_review,
        created_at=now,
    )

    db.add(card)
    db.commit()
    db.refresh(card)
    return card


def _format_span_es(seconds: int) -> str:
    if seconds < 60:
        return f"en {seconds} segundo{'s' if seconds != 1 else ''}"
    if seconds < 3600:
        mins = round(seconds / 60)
        return f"en {mins} minuto{'s' if mins != 1 else ''}"
    if seconds < 86400:
        hours = round(seconds / 3600)
        return f"en {hours} hora{'s' if hours != 1 else ''}"
    days = round(seconds / 86400)
    return f"en {days} día{'s' if days != 1 else ''}"


def _normalize_state(value: Any) -> Optional[State]:
    if value is None:
        return None
    try:
        if isinstance(value, str):
            return State[value]
        return State(int(value))
    except Exception:
        return None


def _ensure_aware_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """Return dt as timezone-aware UTC datetime, or None if dt is None."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        # assume stored as UTC naive -> mark as UTC
        return dt.replace(tzinfo=timezone.utc)
    # already tz-aware -> convert to UTC
    return dt.astimezone(timezone.utc)


def get_card_intervals(db: Session, card_id: int, user_id: UUID) -> CardWithIntervalsResponse:
    # Obtener timezone del usuario
    user_timezone = get_user_timezone(db, user_id)

    # Fecha/hora actual en timezone del usuario
    user_now = to_user_timezone(datetime.now(), user_timezone)
    print("get_card_intervals user timezone:", user_now.tzinfo)

    # Convertir a UTC para FSRS
    now_utc = user_now.astimezone(timezone.utc)
    print("get_card_intervals UTC:", now_utc.tzinfo)

    # Obtener card de la DB
    card_db: Optional[CardDB] = db.query(CardDB).filter(CardDB.id == card_id).first()
    if not card_db:
        raise HTTPException(status_code=404, detail="Card not found")

    # Normalizar state
    state_norm = _normalize_state(getattr(card_db, "state", None)) or State.Learning

    # Construir FSRS Card base (no modifica la DB)
    fsrs_card_base = Card(
        card_id=int(card_db.id),
        state=state_norm,
        step=card_db.step,
        stability=card_db.stability,
        difficulty=card_db.difficulty,
        due=_ensure_aware_utc(card_db.due) or now_utc,  # aseguramos que due nunca sea None
        last_review=_ensure_aware_utc(card_db.last_review),
    )

    # Scheduler determinista
    scheduler = Scheduler(enable_fuzzing=False)

    # Función para simular intervalos según rating
    def _sim_interval_for(rating: Rating) -> str:
        # Crear copia para que no se modifique fsrs_card_base
        simulated_card, _ = scheduler.review_card(
            card=deepcopy(fsrs_card_base),
            rating=rating,
            review_datetime=now_utc,
            review_duration=None,
        )
        due_dt = simulated_card.due or (now_utc + timedelta(seconds=1))
        if due_dt.tzinfo is None:
            due_dt = due_dt.replace(tzinfo=timezone.utc)
        delta_seconds = int((due_dt - now_utc).total_seconds())
        return _format_span_es(delta_seconds)

    intervals = {
        "again": _sim_interval_for(Rating.Again),
        "hard": _sim_interval_for(Rating.Hard),
        "good": _sim_interval_for(Rating.Good),
        "easy": _sim_interval_for(Rating.Easy),
    }

    return CardWithIntervalsResponse(**intervals)

def post_review_card(db: Session, user_id: UUID, request: Any) -> None:
    # --- 1) Obtener timezone del usuario ---
    user_timezone = get_user_timezone(db, user_id)

    # --- 2) Buscar tarjeta por ID ---
    card_db = db.query(CardDB).filter(CardDB.id == int(request.card_id)).first()
    if not card_db:
        raise HTTPException(status_code=404, detail="Card not found")

    if str(card_db.user_id) != str(user_id):
        raise HTTPException(status_code=403, detail="User not allowed to review this card")

    # --- 3) Validar rating ---
    try:
        rating = Rating(int(request.rating))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid rating (must be 1..4)")

    state_norm = _normalize_state(getattr(card_db, "state", None)) or State.Learning

    # --- 4) Construir objeto FSRS Card ---
    now_utc = datetime.now(timezone.utc)
    fsrs_card = Card(
        card_id=int(card_db.id),
        state=state_norm,
        step=card_db.step,
        stability=card_db.stability,
        difficulty=card_db.difficulty,
        due=_ensure_aware_utc(card_db.due) or (now_utc + timedelta(seconds=1)),  # nunca None
        last_review=_ensure_aware_utc(card_db.last_review) or now_utc,
    )

    # --- 5) Scheduler determinista ---
    scheduler = Scheduler(enable_fuzzing=False)

    # --- 6) Fecha/hora de review en timezone del usuario ---
    review_dt = to_user_timezone(datetime.now(), user_timezone)
    print("post_review_card timezone:", review_dt.tzinfo)

    # --- 7) Aplicar la review ---
    updated_fsrs_card, fsrs_review_log = scheduler.review_card(
        card=fsrs_card,
        rating=rating,
        review_datetime=review_dt.astimezone(timezone.utc),  # UTC obligado
        review_duration=None,
    )

    # --- 8) Extraer datos de FSRS review_log ---
    fsrs_dict = fsrs_review_log.to_dict()
    review_dt_from_fsrs = (
        datetime.fromisoformat(fsrs_dict.get("review_datetime")).replace(tzinfo=timezone.utc)
        if fsrs_dict.get("review_datetime")
        else review_dt.astimezone(timezone.utc)
    )
    review_duration_from_fsrs = fsrs_dict.get("review_duration", None)

    # --- 9) Actualizar card en DB ---
    card_db.state = int(updated_fsrs_card.state)
    card_db.step = updated_fsrs_card.step
    card_db.stability = updated_fsrs_card.stability
    card_db.difficulty = updated_fsrs_card.difficulty
    card_db.due = updated_fsrs_card.due
    card_db.last_review = updated_fsrs_card.last_review

    db.add(card_db)
    db.flush()

    # --- 10) Crear review_log ---
    review_log_db = ReviewLogDB(
        card_id=int(card_db.id),
        user_id=user_id,
        rating=int(request.rating),
        review_datetime=review_dt_from_fsrs,
        review_duration=review_duration_from_fsrs,
        write_time_sec=request.write_time_sec,
        stroke_errors=request.stroke_errors,
    )
    db.add(review_log_db)

    # --- 11) Mover o reordenar en DailyFSRSProgress ---
    due_dt = updated_fsrs_card.due or (review_dt + timedelta(seconds=1))
    delta_seconds = (due_dt - review_dt).total_seconds()
    progress_date = review_dt.date()

    daily_progress = (
        db.query(DailyFSRSProgress)
        .filter(DailyFSRSProgress.user_id == user_id,
                DailyFSRSProgress.progress_date == progress_date)
        .first()
    )
    card_id_int = int(card_db.id)

    if daily_progress:
        todays_cards = list(daily_progress.todays_cards or [])
        reviewed_cards = list(daily_progress.reviewed_cards or [])

        # CASO A: intervalo > 1 día -> mover a reviewed_cards
        if delta_seconds >= 86400:
            if card_id_int in todays_cards:
                todays_cards.remove(card_id_int)
            if card_id_int not in reviewed_cards:
                reviewed_cards.append(card_id_int)

        # CASO B: intervalo <= 1 día -> reordenar todays_cards según due
        else:
            id_to_due = {}
            cards_db = db.query(CardDB).filter(CardDB.id.in_(todays_cards)).all()
            id_to_dbcard = {c.id: c for c in cards_db}
            now = review_dt

            def seconds_until_due(cid: int) -> float:
                if cid == card_id_int:
                    due_for_this = updated_fsrs_card.due
                else:
                    db_card = id_to_dbcard.get(cid)
                    due_for_this = db_card.due if db_card else None
                if due_for_this is None:
                    return float("inf")
                return (due_for_this - now).total_seconds()

            todays_cards = sorted(todays_cards, key=seconds_until_due)

        daily_progress.todays_cards = todays_cards
        daily_progress.reviewed_cards = reviewed_cards
        daily_progress.reviewed_count = len(reviewed_cards)
        daily_progress.kanji_count = daily_progress.kanji_count or (len(todays_cards) + len(reviewed_cards))
        daily_progress.completed = daily_progress.reviewed_count >= daily_progress.kanji_count

        db.add(daily_progress)
        db.flush()

    # --- 12) Commit final ---
    db.commit()

def get_today_cards(db: Session, user_id: UUID) -> TodayCardsResponse:
    # Obtener timezone del usuario
    user_timezone = get_user_timezone(db, user_id)

    # Hora local del usuario
    user_now = to_user_timezone(datetime.now(), user_timezone)

    # Fecha local del usuario
    today = user_now.date()

    # 1️⃣ Revisar si ya existe progreso diario
    daily_progress = (
        db.query(DailyFSRSProgress)
        .filter(
            DailyFSRSProgress.user_id == user_id,
            DailyFSRSProgress.progress_date == today,
        )
        .first()
    )

    # 2️⃣ Crear progreso diario si no existe o está vacío
    if not daily_progress or not daily_progress.todays_cards:
        settings = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
        srs_limit = settings.daily_srs_limit if settings else 10

        # Traer todas las cartas del usuario
        cards = db.query(CardDB).filter(CardDB.user_id == user_id).all()
        scheduler = Scheduler(enable_fuzzing=False)

        # Hora UTC para FSRS
        now_utc = user_now.astimezone(timezone.utc)

        # Mapear a FSRS Card y asignar State correcto
        fsrs_cards: list[Card] = []
        for c in cards:
            state = State(c.state) if c.state is not None else State.Learning
            fsrs_cards.append(
                Card(
                    card_id=c.id,
                    state=state,
                    step=c.step,
                    stability=c.stability,
                    difficulty=c.difficulty,
                    due=c.due,
                )
            )

        # Calcular prioridad según tiempo hasta due (UTC)
        def seconds_until_due(card: Card) -> float:
            simulated_card, _ = scheduler.review_card(
                card=card, rating=Rating.Good, review_datetime=now_utc
            )
            due_dt = simulated_card.due or now_utc
            return (due_dt - now_utc).total_seconds()

        # Ordenar por más urgente
        fsrs_cards_sorted = sorted(fsrs_cards, key=seconds_until_due)

        # Tomar hasta el límite
        selected_cards = fsrs_cards_sorted[:srs_limit]
        today_card_ids: list[int] = [card.card_id for card in selected_cards]

        # Si ya existía uno vacío, actualízalo; si no, crea uno nuevo
        if daily_progress:
            daily_progress.kanji_count = len(today_card_ids)
            daily_progress.todays_cards = today_card_ids
            daily_progress.reviewed_cards = []
            daily_progress.completed = False
        else:
            daily_progress = DailyFSRSProgress(
                user_id=user_id,
                progress_date=today,
                kanji_count=len(today_card_ids),
                todays_cards=today_card_ids,
                reviewed_cards=[],
                completed=False,
            )
            db.add(daily_progress)

        db.commit()
        db.refresh(daily_progress)

    # 3️⃣ Recuperar cartas de la DB según IDs
    cards_db = db.query(CardDB).filter(CardDB.id.in_(daily_progress.todays_cards)).all()

    # 4️⃣ Mapear usando Pydantic v2
    todays_cards = [CardResponse.model_validate(c) for c in cards_db]
    reviewed_cards = [
        CardResponse.model_validate(c)
        for c in cards_db
        if c.id in daily_progress.reviewed_cards
    ]

    # 5️⃣ Devolver respuesta
    return TodayCardsResponse(
        todays_cards=todays_cards,
        reviewed_cards=reviewed_cards,
        kanji_count=daily_progress.kanji_count,
        reviewed_count=len(daily_progress.reviewed_cards),
        completed=daily_progress.completed,
    )
