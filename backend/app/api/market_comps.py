from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from app.core.database import get_db
from app.core.permissions import require_partner, require_viewer
from app.models.market_comp import MarketComp

router = APIRouter(prefix="/comps", tags=["market_comps"])


class CompCreate(BaseModel):
    make: str
    model: str
    year: Optional[int] = None
    trim: Optional[str] = None
    mileage: Optional[int] = None
    location: Optional[str] = None
    source: str
    listing_price: float
    sold_price: Optional[float] = None
    url: Optional[str] = None
    date_found: Optional[datetime] = None


@router.post("")
def add_comp(data: CompCreate, db: Session = Depends(get_db), role=Depends(require_partner())):
    comp = MarketComp(**data.model_dump())
    db.add(comp)
    db.commit()
    db.refresh(comp)
    return comp


@router.get("")
def get_comps(
    make: Optional[str] = None,
    model: Optional[str] = None,
    year: Optional[int] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    role=Depends(require_viewer()),
):
    q = db.query(MarketComp)
    if make:
        q = q.filter(MarketComp.make.ilike(f"%{make}%"))
    if model:
        q = q.filter(MarketComp.model.ilike(f"%{model}%"))
    if year:
        q = q.filter(MarketComp.year == year)
    return q.order_by(MarketComp.created_at.desc()).limit(limit).all()


@router.get("/summary")
def comp_summary(
    make: str,
    model: str,
    year: Optional[int] = None,
    db: Session = Depends(get_db),
    role=Depends(require_viewer()),
):
    q = db.query(MarketComp).filter(
        MarketComp.make.ilike(f"%{make}%"),
        MarketComp.model.ilike(f"%{model}%"),
    )
    if year:
        q = q.filter(MarketComp.year == year)
    comps = q.all()
    if not comps:
        return {"count": 0}

    prices = [c.listing_price for c in comps]
    sold = [c.sold_price for c in comps if c.sold_price]
    return {
        "count": len(comps),
        "avg_listing_price": round(sum(prices) / len(prices), 2),
        "median_listing_price": round(sorted(prices)[len(prices) // 2], 2),
        "min_listing_price": min(prices),
        "max_listing_price": max(prices),
        "avg_sold_price": round(sum(sold) / len(sold), 2) if sold else None,
        "sold_count": len(sold),
    }
