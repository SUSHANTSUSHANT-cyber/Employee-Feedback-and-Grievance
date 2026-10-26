from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..database import get_db
from ..auth import require_admin
from ..models import Category, Preset
from ..schemas import PresetIn, PresetOut

router=APIRouter(prefix="/presets",tags=["presets"],dependencies=[Depends(require_admin)])
@router.post("",response_model=PresetOut,status_code=status.HTTP_201_CREATED)
def create(data: PresetIn,db: Session=Depends(get_db)):
    category=db.get(Category,data.categoryName)
    if not category: raise HTTPException(422,"Parent category does not exist")
    if not category.isActive: raise HTTPException(409,"Parent category is inactive")
    item=Preset(**data.model_dump());db.add(item);db.commit();db.refresh(item);return item
@router.get("",response_model=list[PresetOut])
def list_items(category_name: str|None=None,include_inactive: bool=False,db: Session=Depends(get_db)):
    q=select(Preset).order_by(Preset.displayOrder,Preset.id)
    if category_name: q=q.where(Preset.categoryName==category_name)
    if not include_inactive: q=q.where(Preset.isActive.is_(True))
    return db.scalars(q).all()
@router.get("/{preset_id}",response_model=PresetOut)
def get_one(preset_id:int,db:Session=Depends(get_db)):
    item=db.get(Preset,preset_id)
    if not item: raise HTTPException(404,"Preset not found")
    return item
@router.put("/{preset_id}",response_model=PresetOut)
def update_one(preset_id:int,data:PresetIn,db:Session=Depends(get_db)):
    item=db.get(Preset,preset_id)
    if not item: raise HTTPException(404,"Preset not found")
    if not item.isActive: raise HTTPException(409,"Inactive preset must be restored explicitly")
    category=db.get(Category,data.categoryName)
    if not category or not category.isActive: raise HTTPException(422,"An active parent category is required")
    for k,v in data.model_dump().items(): setattr(item,k,v)
    db.commit();db.refresh(item);return item
@router.post("/{preset_id}/deactivate",response_model=PresetOut)
def deactivate(preset_id:int,db:Session=Depends(get_db)):
    item=db.get(Preset,preset_id)
    if not item: raise HTTPException(404,"Preset not found")
    item.isActive=False;db.commit();db.refresh(item);return item
@router.post("/{preset_id}/restore",response_model=PresetOut)
def restore(preset_id:int,db:Session=Depends(get_db)):
    item=db.get(Preset,preset_id)
    if not item: raise HTTPException(404,"Preset not found")
    if not (category:=db.get(Category,item.categoryName)) or not category.isActive: raise HTTPException(409,"Restore the parent category first")
    item.isActive=True;db.commit();db.refresh(item);return item
