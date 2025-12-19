from typing import Any, Optional
from uuid import UUID
from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy.orm import Session

from .fsrs import Card as FsrsCard, Rating, State, Scheduler
from zoneinfo import ZoneInfo

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

    # Obtener timezone del usuario y hora local
    user_timezone = get_user_timezone(db, user_id)
    now_local = to_user_timezone(datetime.now(), user_timezone)

    # Dejamos que la DB asigne el id (autoincrement).
    card = CardDB(
        user_id=user_id,
        kanji_char=kanji_char,
        state=int(State.Learning),
        step=0,
        stability=None,
        difficulty=None,
        due=None,
        last_review=None,
        created_at=now_local,
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


def get_card_intervals(db: Session, card_id: int, user_id: UUID) -> CardWithIntervalsResponse:
    # Obtener timezone del usuario (string, p. ej. "America/La_Paz")
    user_timezone = get_user_timezone(db, user_id)

    # Hora local del usuario
    user_now = to_user_timezone(datetime.now(), user_timezone)

    # Obtener card de la DB
    card_db: Optional[CardDB] = db.query(CardDB).filter(CardDB.id == card_id).first()
    if not card_db:
        raise HTTPException(status_code=404, detail="Card not found")

    # Normalizar state
    state_norm = _normalize_state(getattr(card_db, "state", None)) or State.Learning

    # Construir FSRS Card base (NO modifica la DB)
    # Convertir due/last_review a tz del usuario sólo si existen
    due_local: Optional[datetime] = (
        to_user_timezone(card_db.due, user_timezone) if card_db.due is not None else user_now
    )
    last_review_local: Optional[datetime] = (
        to_user_timezone(card_db.last_review, user_timezone) if card_db.last_review is not None else None
    )

    fsrs_card_base = FsrsCard(
        card_id=int(card_db.id),
        state=state_norm,
        step=card_db.step,
        stability=card_db.stability,
        difficulty=card_db.difficulty,
        due=due_local,
        last_review=last_review_local,
    )

    # Scheduler determinista creado con la zona del usuario
    scheduler = Scheduler(user_tz=ZoneInfo(user_timezone), enable_fuzzing=False)

    # Función para simular intervalos según rating (usando hora local del usuario)
    def _sim_interval_for(rating: Rating) -> str:
        simulated_card, _ = scheduler.review_card(
            card=deepcopy(fsrs_card_base),
            rating=rating,
            review_datetime=user_now,
            review_duration=None,
        )
        due_dt = simulated_card.due or (user_now + timedelta(seconds=1))
        # Ambos en tz del usuario -> resta segura
        delta_seconds = int((due_dt - user_now).total_seconds())
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

    # --- 4) Construir objeto FSRS Card en la TZ del usuario ---
    user_now = to_user_timezone(datetime.now(), user_timezone)

    due_local = (
        to_user_timezone(card_db.due, user_timezone) if card_db.due is not None else (user_now + timedelta(seconds=1))
    )
    last_review_local = (
        to_user_timezone(card_db.last_review, user_timezone) if card_db.last_review is not None else user_now
    )

    fsrs_card = FsrsCard(
        card_id=int(card_db.id),
        state=state_norm,
        step=card_db.step,
        stability=card_db.stability,
        difficulty=card_db.difficulty,
        due=due_local,
        last_review=last_review_local,
    )

    # --- 5) Scheduler determinista en la tz del usuario ---
    scheduler = Scheduler(user_tz=ZoneInfo(user_timezone), enable_fuzzing=False)

    # --- 6) Fecha/hora de review en timezone del usuario ---
    review_dt = to_user_timezone(datetime.now(), user_timezone)

    # --- 7) Aplicar la review (todo en tz del usuario) ---
    updated_fsrs_card, fsrs_review_log = scheduler.review_card(
        card=fsrs_card,
        rating=rating,
        review_datetime=review_dt,
        review_duration=None,
    )

    # --- 8) Extraer datos de FSRS review_log ---
    fsrs_dict = fsrs_review_log.to_dict()
    rd_str = fsrs_dict.get("review_datetime")
    if isinstance(rd_str, str) and rd_str:
        review_dt_from_fsrs_local = datetime.fromisoformat(rd_str)
        if review_dt_from_fsrs_local.tzinfo is None:
            review_dt_from_fsrs_local = review_dt_from_fsrs_local.replace(tzinfo=ZoneInfo(user_timezone))
    else:
        review_dt_from_fsrs_local = review_dt

    review_duration_from_fsrs = fsrs_dict.get("review_duration", None)

    # --- 9) Actualizar card en DB (guardando datetimes en la tz del usuario) ---
    card_db.state = int(updated_fsrs_card.state)
    card_db.step = updated_fsrs_card.step
    card_db.stability = updated_fsrs_card.stability
    card_db.difficulty = updated_fsrs_card.difficulty
    card_db.due = updated_fsrs_card.due
    card_db.last_review = updated_fsrs_card.last_review

    db.add(card_db)
    db.flush()

    # --- 10) Crear review_log (guardamos review_datetime en tz del usuario) ---
    review_log_db = ReviewLogDB(
        card_id=int(card_db.id),
        user_id=user_id,
        rating=int(request.rating),
        review_datetime=review_dt_from_fsrs_local,
        review_duration=review_duration_from_fsrs,
        write_time_sec=getattr(request, "write_time_sec", None),
        stroke_errors=getattr(request, "stroke_errors", None),
    )
    db.add(review_log_db)

    # --- 11) Mover o reordenar en DailyFSRSProgress ---
    due_dt = updated_fsrs_card.due or (review_dt + timedelta(seconds=1))
    delta_seconds = float("inf") if due_dt is None else (due_dt - review_dt).total_seconds()
    progress_date = review_dt.date()

    daily_progress = (
        db.query(DailyFSRSProgress)
        .filter(
            DailyFSRSProgress.user_id == user_id,
            DailyFSRSProgress.progress_date == progress_date,
        )
        .first()
    )
    card_id_int = int(card_db.id)

    if daily_progress:
        # --- Normalizar listas y eliminar None ---
        raw_todays = list(daily_progress.todays_cards or [])
        raw_reviewed = list(daily_progress.reviewed_cards or [])

        def to_int_list(xs):
            out = []
            for x in xs:
                try:
                    if x is None:
                        continue
                    out.append(int(x))
                except Exception:
                    continue
            # dedupe preserving order
            return list(dict.fromkeys(out))

        todays_cards = to_int_list(raw_todays)
        reviewed_cards = to_int_list(raw_reviewed)

        # --- Garantía importante: reviewed_cards nunca debe estar en todays_cards ---
        set_reviewed = set(reviewed_cards)
        todays_cards = [x for x in todays_cards if x not in set_reviewed]

        # --- Operar SOLO sobre card_id_int; no tocar otros elementos salvo reordenarlos ---
        # If the card is in todays_cards -> handle movement or reorder
        if card_id_int in todays_cards:
            # if it was the only one, move to reviewed regardless of interval
            if len(todays_cards) == 1:
                todays_cards.remove(card_id_int)
                if card_id_int not in reviewed_cards:
                    reviewed_cards.append(card_id_int)
            else:
                # long interval -> move to reviewed (unchanged behavior)
                if delta_seconds >= 86400:
                    todays_cards.remove(card_id_int)
                    if card_id_int not in reviewed_cards:
                        reviewed_cards.append(card_id_int)
                else:
                    # short interval -> move this card to the end of todays_cards
                    # (do NOT touch other ids, never inject reviewed ids)
                    try:
                        # remove the id preserving others' order, then append at end
                        todays_cards = [x for x in todays_cards if x != card_id_int]
                        todays_cards.append(card_id_int)
                    except Exception:
                        # defensive fallback: if something unexpected happens don't raise
                        # keep existing order
                        pass
        else:
            # If the card wasn't in todays_cards:
            # - If it is already in reviewed_cards, do nothing (never move it back).
            # - If it's neither in todays nor reviewed, we do not add it to todays here.
            if card_id_int in reviewed_cards:
                pass
            else:
                # Card wasn't scheduled for today — decide policy:
                # If the interval is long, it makes sense to mark it reviewed for today history.
                if delta_seconds >= 86400:
                    if card_id_int not in reviewed_cards:
                        reviewed_cards.append(card_id_int)
                # else: leave lists unchanged

                # IMPORTANT: never add arbitrary ids into todays_cards here.

        # --- Final limpieza: asegurar invariantess ---
        # 1) no duplicates
        todays_cards = [x for x in dict.fromkeys(todays_cards)]
        reviewed_cards = [x for x in dict.fromkeys(reviewed_cards)]
        # 2) ensure disjointness
        set_reviewed = set(reviewed_cards)
        todays_cards = [x for x in todays_cards if x not in set_reviewed]

        # --- Recalcular contadores de forma consistente ---
        reviewed_count = len(reviewed_cards)
        computed_kanji_count = len(todays_cards) + len(reviewed_cards)
        existing_kanji_count = daily_progress.kanji_count or 0
        # keep the larger to avoid accidentally shrinking the target mid-day
        kanji_count = max(existing_kanji_count, computed_kanji_count)

        # cap reviewed_count if it's larger than kanji_count (defensive)
        if reviewed_count > kanji_count:
            reviewed_count = kanji_count


        # --- Aplicar y persistir ---
        daily_progress.todays_cards = todays_cards
        daily_progress.reviewed_cards = reviewed_cards
        daily_progress.reviewed_count = reviewed_count
        daily_progress.kanji_count = kanji_count
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

    # 2️⃣ Crear progreso diario si no existe o está *None* (NO si está vacío list)
    if not daily_progress or daily_progress.todays_cards is None:
        settings = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
        srs_limit = settings.daily_srs_limit if settings else 10

        # Traer todas las cartas del usuario
        cards = db.query(CardDB).filter(CardDB.user_id == user_id).all()

        # Scheduler en la zona del usuario
        scheduler = Scheduler(user_tz=ZoneInfo(user_timezone), enable_fuzzing=False)

        # Hora local del usuario (usar user_now ya calculado arriba)
        now_local = user_now

        # Mapear a FSRS Card y asignar State correcto (debemos pasar due en tz del usuario)
        fsrs_cards: list[FsrsCard] = []
        for c in cards:
            state = State(c.state) if c.state is not None else State.Learning
            due_local_c = to_user_timezone(c.due, user_timezone) if c.due is not None else None
            last_review_local_c = to_user_timezone(c.last_review, user_timezone) if c.last_review is not None else None

            fsrs_cards.append(
                FsrsCard(
                    card_id=c.id,
                    state=state,
                    step=c.step,
                    stability=c.stability,
                    difficulty=c.difficulty,
                    due=due_local_c,
                    last_review=last_review_local_c,
                )
            )

        # Calcular prioridad según tiempo hasta due (en la tz del usuario)
        def seconds_until_due(card: FsrsCard) -> float:
            simulated_card, _ = scheduler.review_card(
                card=card, rating=Rating.Good, review_datetime=now_local
            )
            due_dt = simulated_card.due or now_local
            return (due_dt - now_local).total_seconds()

        # Ordenar por más urgente
        fsrs_cards_sorted = sorted(fsrs_cards, key=seconds_until_due)

        # Tomar hasta el límite
        selected_cards = fsrs_cards_sorted[:srs_limit]
        today_card_ids: list[int] = [card.card_id for card in selected_cards]

        # Si ya existía uno vacío (daily_progress) que tenía todays_cards == None, actualízalo;
        # si no, crea uno nuevo
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

    # 3️⃣ Recuperar cartas de la DB según IDs — PRESERVANDO EL ORDEN ALMACENADO EN daily_progress
    todays_ids = list(daily_progress.todays_cards or [])
    reviewed_ids = list(daily_progress.reviewed_cards or [])

    # Dedupe y construir la lista total de ids a buscar para minimizar consultas
    all_ids = list(dict.fromkeys(todays_ids + reviewed_ids))

    if all_ids:
        cards_fetched = db.query(CardDB).filter(CardDB.id.in_(all_ids)).all()
    else:
        cards_fetched = []

    # Map id -> DB row
    id_to_card = {c.id: c for c in cards_fetched}

    # Reconstruir listas EN EL ORDEN EXACTO de daily_progress
    todays_cards = [CardResponse.model_validate(id_to_card[i]) for i in todays_ids if i in id_to_card]
    reviewed_cards = [CardResponse.model_validate(id_to_card[i]) for i in reviewed_ids if i in id_to_card]

    # 5️⃣ Devolver respuesta
    return TodayCardsResponse(
        todays_cards=todays_cards,
        reviewed_cards=reviewed_cards,
        kanji_count=daily_progress.kanji_count,
        reviewed_count=len(daily_progress.reviewed_cards or []),
        completed=daily_progress.completed,
    )




def increase_daily_kanji(db: Session, user_id: UUID, add_count: int):
    if add_count <= 0:
        raise HTTPException(status_code=400, detail="add_count must be > 0")

    user_tz = get_user_timezone(db, user_id)
    today = to_user_timezone(datetime.now(), user_tz).date()

    # 1) Buscar todos los progresos del usuario
    progresses = (
        db.query(DailyFSRSProgress)
        .filter(DailyFSRSProgress.user_id == user_id)
        .all()
    )

    # Si NO existe ninguno → crear uno nuevo para hoy
    if not progresses:
        daily_progress = DailyFSRSProgress(
            user_id=user_id,
            progress_date=today,
            kanji_count=0,
            todays_cards=[],
            reviewed_cards=[],
            completed=False,
        )
        db.add(daily_progress)
        db.commit()
        db.refresh(daily_progress)
    else:
        # Elegir el registro con fecha más cercana a hoy (defensivo)
        def days_diff(p: DailyFSRSProgress) -> int:
            pd = getattr(p, "progress_date", None)
            try:
                return abs(pd.toordinal() - today.toordinal())
            except Exception:
                # Si algo raro ocurre (None u otro tipo), devolver un número grande
                return 10 ** 6

        daily_progress = min(progresses, key=days_diff)

    # 2) Marcar como no completado
    daily_progress.completed = False

    # 3) Normalizar listas (int, quitar None, dedupe)
    def normalize(xs):
        out = []
        for x in (xs or []):
            try:
                if x is None:
                    continue
                out.append(int(x))
            except Exception:
                continue
        return list(dict.fromkeys(out))

    todays = normalize(daily_progress.todays_cards)
    reviewed = normalize(daily_progress.reviewed_cards)

    set_todays = set(todays)
    set_reviewed = set(reviewed)

    # 4) Obtener TODOS los cards del usuario en orden determinista:
    #    due NOT NULL first, then due asc, then created_at asc
    all_cards = (
        db.query(CardDB.id)
        .filter(CardDB.user_id == user_id)
        .order_by(
            CardDB.due.is_(None),  # False (has due) first, True (no due) last
            CardDB.due,
            CardDB.created_at,
        )
        .all()
    )
    # all_cards items son tuplas como (id,), por eso r[0]
    all_ids = [int(r[0]) for r in all_cards]

    # 5) Candidatos nuevos (no en todays, no en reviewed)
    candidates = [cid for cid in all_ids if cid not in set_todays and cid not in set_reviewed]

    to_add = []

    # 6) Primero intentar llenar con candidatos nuevos
    take_cand = min(add_count, len(candidates))
    if take_cand > 0:
        to_add.extend(candidates[:take_cand])

    remaining = add_count - len(to_add)

    # 7) Si faltan -> tomar desde reviewed_cards (solo en este caso)
    if remaining > 0 and reviewed:
        take_from_rev = min(remaining, len(reviewed))
        if take_from_rev > 0:
            moved = reviewed[:take_from_rev]
            to_add.extend(moved)
            reviewed = reviewed[take_from_rev:]  # remover los usados

    # 8) Añadir a todays_cards sin duplicar
    for cid in to_add:
        if cid not in set_todays:
            todays.append(cid)
            set_todays.add(cid)

    # 9) Limpieza final: dedupe y asegurar disjointness
    todays = [x for x in dict.fromkeys(todays)]
    reviewed = [x for x in dict.fromkeys(reviewed)]
    todays = [x for x in todays if x not in set(reviewed)]

    # 10) Recalcular contadores
    reviewed_count = len(reviewed)
    kanji_count = max(daily_progress.kanji_count or 0, len(todays) + len(reviewed))

    # 11) Persistir cambios
    daily_progress.todays_cards = todays
    daily_progress.reviewed_cards = reviewed
    daily_progress.reviewed_count = reviewed_count
    daily_progress.kanji_count = kanji_count
    daily_progress.completed = False

    db.add(daily_progress)
    db.commit()
    db.refresh(daily_progress)
