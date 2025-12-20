from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app import models, schemas
from app.db import get_db
from app.routes.auth import get_current_user

router = APIRouter(prefix="/season", tags=["season"])


@router.post("/start", response_model=schemas.SeasonOut)
def start_season(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _ = current_user
    last_season = db.query(models.Season).order_by(desc(models.Season.number)).first()
    next_number = last_season.number + 1 if last_season else 1

    now = datetime.now(timezone.utc)
    season = models.Season(
        number=next_number,
        starts_at=now,
        ends_at=now + timedelta(days=14),
        is_active=True,
    )

    db.query(models.Season).filter(models.Season.is_active == True).update(  # noqa: E712
        {models.Season.is_active: False}
    )
    db.add(season)
    db.query(models.User).update({models.User.prestige: 1000})
    db.commit()
    db.refresh(season)

    return season
