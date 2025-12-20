from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.db import get_db
from app.pvp_constants import SERVER_TZ
from app.routes.auth import get_current_user

router = APIRouter(tags=["army"])


def _now() -> datetime:
    return datetime.now(SERVER_TZ)


def _get_barracks_or_404(db: Session, user_id) -> models.UserBuilding:
    building = (
        db.query(models.UserBuilding)
        .filter(
            models.UserBuilding.user_id == user_id,
            models.UserBuilding.building_type == "barracks",
        )
        .first()
    )
    if not building:
        raise HTTPException(status_code=404, detail="Barracks not found")
    return building


def _get_unit_type_or_404(db: Session, code: str) -> models.UnitType:
    unit_type = db.query(models.UnitType).filter(models.UnitType.code == code).first()
    if not unit_type:
        raise HTTPException(status_code=404, detail="Unit type not found")
    return unit_type


def _set_job_done_if_ready(db: Session, job: models.TrainingJob) -> models.TrainingJob:
    if job.status == "running" and _now() >= job.completes_at:
        job.status = "done"
        db.add(job)
    return job


@router.get("/army", response_model=schemas.ArmyOut)
def get_army(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    unit_types = db.query(models.UnitType).order_by(models.UnitType.id).all()

    units = []
    for unit_type in unit_types:
        user_unit = (
            db.query(models.UserUnit)
            .filter(
                models.UserUnit.user_id == current_user.id,
                models.UserUnit.unit_type_id == unit_type.id,
            )
            .first()
        )
        units.append(
            schemas.ArmyUnitOut(
                code=unit_type.code,
                qty=user_unit.qty if user_unit else 0,
            )
        )

    return schemas.ArmyOut(units=units)


@router.post("/barracks/train", response_model=schemas.BarracksTrainOut)
def barracks_train(
    payload: schemas.BarracksTrainIn,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _get_barracks_or_404(db, current_user.id)
    unit_type = _get_unit_type_or_404(db, payload.unit_code)

    running = (
        db.query(models.TrainingJob)
        .filter(
            models.TrainingJob.user_id == current_user.id,
            models.TrainingJob.status == "running",
        )
        .first()
    )
    if running:
        raise HTTPException(status_code=409, detail="Training queue is busy")

    started_at = _now()
    completes_at = started_at + timedelta(
        seconds=unit_type.train_time_sec * payload.qty
    )

    job = models.TrainingJob(
        user_id=current_user.id,
        unit_type_id=unit_type.id,
        qty=payload.qty,
        started_at=started_at,
        completes_at=completes_at,
        status="running",
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    return schemas.BarracksTrainOut(
        job_id=job.id,
        status="running",
        unit_code=unit_type.code,
        qty=job.qty,
        started_at=job.started_at,
        completes_at=job.completes_at,
    )


@router.get("/barracks/queue", response_model=schemas.BarracksQueueOut)
def barracks_queue(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    job = (
        db.query(models.TrainingJob)
        .filter(
            models.TrainingJob.user_id == current_user.id,
            models.TrainingJob.status.in_(["running", "done"]),
        )
        .order_by(models.TrainingJob.id.desc())
        .first()
    )

    if not job:
        return schemas.BarracksQueueOut(status=None)

    job = _set_job_done_if_ready(db, job)
    db.commit()

    unit_type = db.query(models.UnitType).filter(models.UnitType.id == job.unit_type_id).first()
    return schemas.BarracksQueueOut(
        status=job.status if job.status in ["running", "done"] else None,
        job_id=job.id,
        unit_code=unit_type.code if unit_type else None,
        qty=job.qty,
        started_at=job.started_at,
        completes_at=job.completes_at,
    )


@router.post("/barracks/claim", response_model=schemas.BarracksClaimOut)
def barracks_claim(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    job = (
        db.query(models.TrainingJob)
        .filter(
            models.TrainingJob.user_id == current_user.id,
            models.TrainingJob.status.in_(["running", "done"]),
        )
        .order_by(models.TrainingJob.id.desc())
        .first()
    )

    if not job:
        return schemas.BarracksClaimOut(claimed=False)

    job = _set_job_done_if_ready(db, job)
    if job.status != "done":
        db.commit()
        return schemas.BarracksClaimOut(claimed=False)

    unit_type = db.query(models.UnitType).filter(models.UnitType.id == job.unit_type_id).first()
    if not unit_type:
        raise HTTPException(status_code=500, detail="Unit type missing for job")

    user_unit = (
        db.query(models.UserUnit)
        .filter(
            models.UserUnit.user_id == current_user.id,
            models.UserUnit.unit_type_id == unit_type.id,
        )
        .first()
    )

    now = _now()
    if not user_unit:
        user_unit = models.UserUnit(
            user_id=current_user.id,
            unit_type_id=unit_type.id,
            qty=0,
            updated_at=now,
        )

    user_unit.qty += job.qty
    user_unit.updated_at = now
    job.status = "claimed"

    db.add(user_unit)
    db.add(job)
    db.commit()

    return schemas.BarracksClaimOut(
        claimed=True,
        unit_code=unit_type.code,
        qty=job.qty,
        job_id=job.id,
    )
