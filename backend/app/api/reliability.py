from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.core.database import get_db
from app.core.permissions import require_partner, require_viewer
from app.models.reliability_score import ReliabilityScore
from app.services.scoring import get_reliability_score

router = APIRouter(prefix="/reliability", tags=["reliability"])


class ReliabilityUpdate(BaseModel):
    score: float
    notes: Optional[str] = None


@router.get("")
def get_all(db: Session = Depends(get_db), role=Depends(require_viewer())):
    return db.query(ReliabilityScore).order_by(ReliabilityScore.make, ReliabilityScore.model).all()


@router.get("/lookup")
def lookup(make: str, model: Optional[str] = None, db: Session = Depends(get_db), role=Depends(require_viewer())):
    score = get_reliability_score(make, model, db)
    return {"make": make, "model": model, "score": score}


@router.patch("/{rid}")
def update_score(rid: int, data: ReliabilityUpdate, db: Session = Depends(get_db), role=Depends(require_partner())):
    row = db.query(ReliabilityScore).filter(ReliabilityScore.id == rid).first()
    if not row:
        raise HTTPException(status_code=404, detail="Not found")
    row.score = data.score
    if data.notes:
        row.notes = data.notes
    db.commit()
    db.refresh(row)
    return row
