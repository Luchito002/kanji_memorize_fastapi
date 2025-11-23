from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import IntEnum
from typing import Optional, Tuple, Dict, Any
from zoneinfo import ZoneInfo


class State(IntEnum):
    """Minimal set of states. Values are integers so existing DB ints remain usable.
    You can extend these later if you migrated values from another FSRS library.
    """
    New = 0
    Learning = 1
    Review = 2
    Mature = 3


class Rating(IntEnum):
    # Keep numeric mapping compatible with code that casts Rating(int(request.rating))
    Again = 1
    Hard = 2
    Good = 3
    Easy = 4


@dataclass
class Card:
    """Lightweight FSRS Card used by scheduler.

    Fields chosen to match what the application code expects:
      - card_id: int
      - state: State
      - step: Optional[int]
      - stability: Optional[float]
      - difficulty: Optional[float]
      - due: Optional[datetime] (timezone-aware in the user's timezone)
      - last_review: Optional[datetime] (timezone-aware in the user's timezone)

    IMPORTANT: All datetimes handled by the Scheduler are in the *user's timezone*.
    """

    card_id: int
    state: State = State.Learning
    step: Optional[int] = None
    stability: Optional[float] = None
    difficulty: Optional[float] = None
    due: Optional[datetime] = None
    last_review: Optional[datetime] = None


@dataclass
class ReviewLog:
    rating: Rating
    review_datetime: datetime
    review_duration: Optional[float] = None
    extra: Optional[Dict[str, Any]] = None

    def to_dict(self) -> dict:
        d: Dict[str, Any] = {
            "rating": int(self.rating),
            # ISO format with timezone info
            "review_datetime": self.review_datetime.isoformat()
            if self.review_datetime is not None
            else None,
            "review_duration": self.review_duration,
        }
        if self.extra:
            d.update(self.extra)
        return d


class Scheduler:
    """Scheduler that operates entirely in a *user-specific timezone*.

    Design decisions:
    - The scheduler **requires** the user's timezone (zoneinfo.ZoneInfo) at init.
    - All inputs and outputs (review_datetime, due, last_review) are timezone-aware
      datetimes in the *user's timezone*.
    - This avoids midnight/UTC confusion and keeps '1 day' semantics aligned with
      the user's local clock.

    Usage:
        from zoneinfo import ZoneInfo
        scheduler = Scheduler(user_tz=ZoneInfo(user.timezone))
        updated, log = scheduler.review_card(card, rating, review_datetime=user_local_dt)

    """

    def __init__(self, user_tz: ZoneInfo, enable_fuzzing: bool = False):
        self.user_tz = user_tz
        # keep api parity
        self.enable_fuzzing = enable_fuzzing

    def _ensure_aware_in_user_tz_or_none(self, dt: Optional[datetime]) -> Optional[datetime]:
        if dt is None:
            return None
        if dt.tzinfo is None:
            # treat naive datetimes as if they are already in user timezone
            return dt.replace(tzinfo=self.user_tz)
        return dt.astimezone(self.user_tz)

    def _ensure_aware_in_user_tz(self, dt: datetime) -> datetime:
        if dt.tzinfo is None:
            return dt.replace(tzinfo=self.user_tz)
        return dt.astimezone(self.user_tz)

    def review_card(
        self,
        card: Card,
        rating: Rating,
        review_datetime: Optional[datetime] = None,
        review_duration: Optional[float] = None,
    ) -> Tuple[Card, ReviewLog]:
        """Apply a review and return a new Card (do not mutate the input) plus a ReviewLog.

        Important: `review_datetime` should be either None or a datetime in the user's
        timezone (tz-aware). If None, the current time in user's timezone is used.

        Returns updated Card with `due` and `last_review` expressed in the user's timezone.
        """
        # now_in is aware in user tz
        now_in = review_datetime or datetime.now(self.user_tz)
        now = self._ensure_aware_in_user_tz(now_in)

        # copy input to avoid mutating caller's object; normalize None -> sensible defaults
        updated = Card(
            card_id=int(card.card_id),
            state=card.state if card.state is not None else State.Learning,
            step=(card.step if card.step is not None else 0),
            stability=(card.stability if card.stability is not None else 0.0),
            difficulty=(card.difficulty if card.difficulty is not None else 0.3),
            due=self._ensure_aware_in_user_tz_or_none(card.due),
            last_review=self._ensure_aware_in_user_tz_or_none(card.last_review),
        )

        # coerce to local numeric vars so static type checkers know they're not None
        stability = float(updated.stability or 0.0)
        difficulty = float(updated.difficulty or 0.3)
        step = int(updated.step or 0)

        # Basic sanity bounds
        difficulty = max(0.05, min(0.95, difficulty))

        # Time since last review (seconds), may be 0
        # annotate types for static analysis: `now` is a datetime in user tz
        from typing import Optional as _Optional
        now: datetime = now  # type: ignore[assignment]
        last_rev: _Optional[datetime] = updated.last_review
        if last_rev is not None:
            # ensure static analyzer knows both operands are datetimes
            elapsed = (now - last_rev).total_seconds()
        else:
            elapsed = 0.0

        # Heuristic update rules (simple, deterministic)
        if rating == Rating.Again:
            # Strong reset / learning step
            new_state = State.Learning
            new_step = 1
            # punish stability
            new_stability = max(0.05, stability * 0.5)
            # increase difficulty slightly
            new_difficulty = min(0.95, difficulty + 0.03)
            # schedule soon: 10 minutes in user tz
            next_due = now + timedelta(minutes=10)

        elif rating == Rating.Hard:
            # Hard: small gain
            new_state = State.Review
            new_step = step + 1
            new_stability = (stability or 0.1) * 1.2
            new_difficulty = min(0.95, difficulty + 0.01)
            # schedule within hours
            next_due = now + timedelta(hours=6)

        elif rating == Rating.Good:
            # Good: normal progression
            new_state = State.Review
            new_step = step + 1
            # stability increases proportionally to elapsed time and current stability
            factor = 2.0 + min(elapsed / 86400.0, 5.0)
            new_stability = max(0.1, stability * factor)
            new_difficulty = max(0.05, difficulty - 0.01)
            # schedule next day (or longer if stability large)
            interval_days = max(1, int(round(new_stability * 1.5)))
            next_due = now + timedelta(days=interval_days)

        else:  # Rating.Easy
            new_state = State.Mature
            new_step = step + 2
            new_stability = max(0.2, stability * 3.0)
            new_difficulty = max(0.05, difficulty - 0.02)
            # longer spacing for Easy
            interval_days = max(2, int(round(new_stability * 2.0)))
            next_due = now + timedelta(days=interval_days)

        # Finalize updated fields (all in user's timezone)
        updated.state = new_state
        updated.step = new_step
        updated.stability = float(new_stability)
        updated.difficulty = float(new_difficulty)
        updated.due = self._ensure_aware_in_user_tz(next_due)
        updated.last_review = now

        # Build a review log; include elapsed to mark it as used
        log = ReviewLog(
            rating=rating,
            review_datetime=now,
            review_duration=review_duration,
            extra={
                "prev_stability": stability,
                "new_stability": updated.stability,
                "prev_difficulty": difficulty,
                "new_difficulty": updated.difficulty,
                "prev_step": step,
                "new_step": updated.step,
                "prev_state": int(card.state) if card.state is not None else None,
                "new_state": int(updated.state),
                "elapsed_seconds": elapsed,
            },
        )

        return updated, log
