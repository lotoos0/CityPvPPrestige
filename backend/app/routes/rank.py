from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import models, schemas
from app.db import get_db
from app.routes.auth import get_current_user

router = APIRouter(prefix="/rank", tags=["rank"])


def get_or_create_city(db: Session, user: models.User) -> models.City:
    city = db.query(models.City).filter(models.City.user_id == user.id).first()
    if city:
        return city

    city = models.City(user_id=user.id)
    db.add(city)
    db.commit()
    db.refresh(city)
    return city


def fetch_ranked(db: Session) -> list[tuple[models.City, models.User]]:
    return (
        db.query(models.City, models.User)
        .join(models.User, models.City.user_id == models.User.id)
        .order_by(models.City.prestige.desc())
        .all()
    )


@router.get("/top", response_model=list[schemas.RankEntry])
def top_rank(db: Session = Depends(get_db)):
    ranked = fetch_ranked(db)[:10]
    results = []
    for idx, (city, user) in enumerate(ranked, start=1):
        results.append(
            schemas.RankEntry(
                rank=idx,
                user_id=user.id,
                email=user.email,
                prestige=city.prestige,
            )
        )
    return results


@router.get("/near", response_model=list[schemas.RankEntry])
def near_rank(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    get_or_create_city(db, current_user)
    ranked = fetch_ranked(db)

    user_index = 0
    for idx, (_, user) in enumerate(ranked):
        if user.id == current_user.id:
            user_index = idx
            break

    start = max(user_index - 3, 0)
    end = min(user_index + 4, len(ranked))

    results = []
    for idx, (city, user) in enumerate(ranked[start:end], start=start + 1):
        results.append(
            schemas.RankEntry(
                rank=idx,
                user_id=user.id,
                email=user.email,
                prestige=city.prestige,
            )
        )
    return results
