from datetime import datetime
from typing import Optional

from sqlalchemy.exc import IntegrityError

from app import models
from app.db import SessionLocal
from app.pvp_constants import (
    DAILY_DECAY_MAX,
    DAILY_DECAY_RATE,
    DECAY_THRESHOLD,
    INACTIVITY_GRACE,
    INACTIVITY_MULT,
    SERVER_TZ,
)


def calculate_inactive_days(now: datetime, last_pvp_at: Optional[datetime]) -> int:
    if last_pvp_at is None:
        return 999
    return (now.date() - last_pvp_at.astimezone(SERVER_TZ).date()).days


def run_nightly_decay() -> int:
    db = SessionLocal()
    try:
        now = datetime.now(SERVER_TZ)
        today = now.date()

        tick = models.SystemTick(tick_name="nightly_decay", tick_day=today)
        db.add(tick)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            return 0

        decayed = 0
        users = db.query(models.User).yield_per(1000)
        for user in users:
            excess = max(0, user.prestige - DECAY_THRESHOLD)
            if excess == 0:
                continue

            inactive_days = calculate_inactive_days(now, user.last_pvp_at)
            rate = DAILY_DECAY_RATE
            if inactive_days >= INACTIVITY_GRACE:
                rate *= INACTIVITY_MULT

            decay = round(min(DAILY_DECAY_MAX, excess * rate))
            if decay <= 0:
                continue

            prestige_before = user.prestige
            user.prestige = prestige_before - decay
            db.add(
                models.PrestigeDecayLog(
                    user_id=user.id,
                    day=today,
                    prestige_before=prestige_before,
                    prestige_after=user.prestige,
                    decay_amount=decay,
                    inactive_days=inactive_days,
                    rate_used=rate,
                )
            )
            decayed += 1

        db.commit()
        return decayed
    finally:
        db.close()


if __name__ == "__main__":
    count = run_nightly_decay()
    print(f"Nightly decay applied to {count} users.")
