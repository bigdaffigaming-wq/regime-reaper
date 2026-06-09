from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List

from app.core.database import get_db
from app.core.permissions import require_partner, require_viewer
from app.models.repair import RepairCost

router = APIRouter(prefix="/repairs", tags=["repairs"])


class RepairCreate(BaseModel):
    category: str
    repair_name: str
    low_cost: float
    high_cost: float
    avg_cost: float
    labor_hours: Optional[float] = None
    severity: str = "medium"
    notes: Optional[str] = None


class RepairUpdate(BaseModel):
    low_cost: Optional[float] = None
    high_cost: Optional[float] = None
    avg_cost: Optional[float] = None
    severity: Optional[str] = None
    notes: Optional[str] = None


@router.get("")
def get_repairs(db: Session = Depends(get_db), role=Depends(require_viewer())):
    return db.query(RepairCost).order_by(RepairCost.category, RepairCost.repair_name).all()


@router.post("")
def create_repair(data: RepairCreate, db: Session = Depends(get_db), role=Depends(require_partner())):
    repair = RepairCost(**data.model_dump())
    db.add(repair)
    db.commit()
    db.refresh(repair)
    return repair


@router.patch("/{repair_id}")
def update_repair(repair_id: int, data: RepairUpdate, db: Session = Depends(get_db), role=Depends(require_partner())):
    repair = db.query(RepairCost).filter(RepairCost.id == repair_id).first()
    if not repair:
        raise HTTPException(status_code=404, detail="Repair not found")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(repair, field, value)
    db.commit()
    db.refresh(repair)
    return repair
