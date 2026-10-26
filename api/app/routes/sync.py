from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import (
    AdminConfig,
    Category,
    DeletedGrievance,
    Employee,
    InteractionLog,
    Preset,
)
from ..schemas import SyncSnapshot


router = APIRouter(tags=["sync"])


@router.get("/sync", response_model=SyncSnapshot)
@router.post("/sync", response_model=SyncSnapshot)
def sync(db: Session = Depends(get_db)):

    categories = db.scalars(
        select(Category)
        .where(Category.isActive.is_(True))
        .order_by(Category.displayOrder)
    ).all()

    active_names = [category.name for category in categories]

    employees = db.scalars(
        select(Employee)
        .where(Employee.isActive.is_(True))
    ).all()

    presets = (
        db.scalars(
            select(Preset)
            .where(
                Preset.isActive.is_(True),
                Preset.categoryName.in_(active_names)
            )
            .order_by(Preset.displayOrder)
        ).all()
        if active_names
        else []
    )

    interaction_logs = db.scalars(
        select(InteractionLog)
        .order_by(InteractionLog.timestamp.desc())
    ).all()

    deleted_complaint_numbers = db.scalars(
        select(DeletedGrievance.complaintNumber)
    ).all()

    admin_config = db.get(AdminConfig, 1)

    return SyncSnapshot(
        employees=employees,
        custom_categories=categories,
        custom_presets=presets,
        admin_config=[admin_config] if admin_config else [],
        interaction_logs=interaction_logs,
        deleted_complaint_numbers=deleted_complaint_numbers,
    )