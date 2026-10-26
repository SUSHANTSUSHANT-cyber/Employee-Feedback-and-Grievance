from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..auth import require_admin
from ..models import AdminConfig
from ..schemas import AdminConfigIn, AdminConfigOut


router = APIRouter(
    prefix="/admin-config",
    tags=["admin config"],
    dependencies=[Depends(require_admin)],
)


@router.get("", response_model=AdminConfigOut | None)
def get_config(db: Session = Depends(get_db)):
    return db.get(AdminConfig, 1)


@router.post(
    "",
    response_model=AdminConfigOut,
    status_code=status.HTTP_201_CREATED
)
def create(
    data: AdminConfigIn,
    db: Session = Depends(get_db)
):
    if db.get(AdminConfig, 1):
        raise HTTPException(
            status_code=409,
            detail="Configuration already exists"
        )

    item = AdminConfig(
        id=1,
        **data.model_dump()
    )

    db.add(item)
    db.commit()
    db.refresh(item)

    return item


@router.put("", response_model=AdminConfigOut)
def update(
    data: AdminConfigIn,
    db: Session = Depends(get_db)
):
    item = db.get(AdminConfig, 1)

    if not item:
        raise HTTPException(
            status_code=404,
            detail="Configuration does not exist; create it first"
        )

    for key, value in data.model_dump().items():
        setattr(item, key, value)

    db.commit()
    db.refresh(item)

    return item
