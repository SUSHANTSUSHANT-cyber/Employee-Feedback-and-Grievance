from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session
from ..database import get_db
from ..auth import require_admin
from ..models import Category, Preset
from ..schemas import CategoryIn, CategoryOut

router = APIRouter(prefix="/categories", tags=["categories"], dependencies=[Depends(require_admin)])

@router.post("", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
def create(data: CategoryIn, db: Session = Depends(get_db)):
    if db.get(Category, data.name): 
        raise HTTPException(409, "Category already exists; restore it explicitly if inactive.")
    item = Category(**data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

@router.get("", response_model=list[CategoryOut])
def list_items(include_inactive: bool = False, db: Session = Depends(get_db)):
    q = select(Category).order_by(Category.displayOrder, Category.name)
    if not include_inactive: 
        q = q.where(Category.isActive.is_(True))
    return db.scalars(q).all()

@router.get("/{name}", response_model=CategoryOut)
def get_one(name: str, db: Session = Depends(get_db)):
    item = db.get(Category, name)
    if not item: 
        raise HTTPException(404, "Category not found")
    return item

@router.put("/{name}", response_model=CategoryOut)
def update_one(name: str, data: CategoryIn, db: Session = Depends(get_db)):
    item = db.get(Category, name)
    if not item: 
        raise HTTPException(404, "Category not found")
    if not item.isActive: 
        raise HTTPException(409, "Inactive category must be restored explicitly")
    if data.name != name and db.get(Category, data.name): 
        raise HTTPException(409, "Category name already exists")
    
    # Update all fields from the request
    for k, v in data.model_dump().items(): 
        setattr(item, k, v)
    
    db.commit()
    db.refresh(item)
    return item

@router.post("/{name}/deactivate", response_model=CategoryOut)
def deactivate(name: str, db: Session = Depends(get_db)):
    item = db.get(Category, name)
    if not item: 
        raise HTTPException(404, "Category not found")
    try:
        item.isActive = False
        db.execute(update(Preset).where(Preset.categoryName == name).values(isActive=False))
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(item)
    return item

@router.post("/{name}/restore", response_model=CategoryOut)
def restore(name: str, db: Session = Depends(get_db)):
    item = db.get(Category, name)
    if not item: 
        raise HTTPException(404, "Category not found")
    item.isActive = True
    db.commit()
    db.refresh(item)
    return item
