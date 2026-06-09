from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.core.database import get_db
from app.core.permissions import require_partner, require_viewer
from app.models.negotiation import Negotiation

router = APIRouter(prefix="/negotiations", tags=["negotiations"])


class NegotiationCreate(BaseModel):
    listing_id: int
    initial_price: float
    offer_price: Optional[float] = None
    notes: Optional[str] = None


class NegotiationUpdate(BaseModel):
    offer_price: Optional[float] = None
    counter_offer: Optional[float] = None
    accepted_price: Optional[float] = None
    notes: Optional[str] = None
    status: Optional[str] = None


@router.post("")
def create_negotiation(data: NegotiationCreate, db: Session = Depends(get_db), role=Depends(require_partner())):
    neg = Negotiation(**data.model_dump())
    db.add(neg)
    db.commit()
    db.refresh(neg)
    return neg


@router.get("")
def get_negotiations(listing_id: Optional[int] = None, db: Session = Depends(get_db), role=Depends(require_viewer())):
    q = db.query(Negotiation)
    if listing_id:
        q = q.filter(Negotiation.listing_id == listing_id)
    return q.order_by(Negotiation.created_at.desc()).all()


@router.patch("/{neg_id}")
def update_negotiation(neg_id: int, data: NegotiationUpdate, db: Session = Depends(get_db), role=Depends(require_partner())):
    neg = db.query(Negotiation).filter(Negotiation.id == neg_id).first()
    if not neg:
        raise HTTPException(status_code=404, detail="Negotiation not found")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(neg, field, value)
    db.commit()
    db.refresh(neg)
    return neg


@router.get("/stats")
def negotiation_stats(db: Session = Depends(get_db), role=Depends(require_viewer())):
    negs = db.query(Negotiation).all()
    if not negs:
        return {"count": 0}

    accepted = [n for n in negs if n.accepted_price and n.initial_price]
    savings = [n.initial_price - n.accepted_price for n in accepted]
    return {
        "total": len(negs),
        "accepted": len(accepted),
        "declined": len([n for n in negs if n.status == "declined"]),
        "acceptance_rate": round(len(accepted) / len(negs) * 100, 1) if negs else 0,
        "avg_savings": round(sum(savings) / len(savings), 2) if savings else 0,
        "total_savings": round(sum(savings), 2) if savings else 0,
    }
