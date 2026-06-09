from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.permissions import require_partner, require_viewer
from app.models.inventory import Inventory
from app.models.listing import Listing
from app.schemas.inventory import InventoryCreate, InventoryUpdate, InventoryMarkSold, InventoryOut
from app.services.audit_logger import log_action

router = APIRouter(prefix="/inventory", tags=["inventory"])


def _calc_total_invested(inv: Inventory) -> float:
    return (
        inv.purchase_price
        + inv.repair_cost_actual
        + inv.cleaning_cost_actual
        + inv.title_fees
        + inv.misc_costs
    )


@router.post("/from-listing/{listing_id}", response_model=InventoryOut)
def create_from_listing(
    listing_id: int,
    data: InventoryCreate,
    db: Session = Depends(get_db),
    role=Depends(require_partner()),
):
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    if db.query(Inventory).filter(Inventory.listing_id == listing_id).first():
        raise HTTPException(status_code=400, detail="Inventory item already exists for this listing")

    total_invested = (
        data.purchase_price
        + data.repair_cost_actual
        + data.cleaning_cost_actual
        + data.title_fees
        + data.misc_costs
    )

    inv = Inventory(
        listing_id=listing_id,
        purchase_price=data.purchase_price,
        repair_cost_actual=data.repair_cost_actual,
        cleaning_cost_actual=data.cleaning_cost_actual,
        title_fees=data.title_fees,
        misc_costs=data.misc_costs,
        total_invested=total_invested,
        date_bought=datetime.now(timezone.utc),
        inventory_status="bought",
        notes=data.notes,
    )
    db.add(inv)

    # Update listing status
    listing.status = "bought"
    db.commit()
    db.refresh(inv)

    log_action(db, "inventory_created", source="dashboard", entity_type="inventory", entity_id=inv.id,
               new_value={"purchase_price": data.purchase_price, "listing_id": listing_id})
    return inv


@router.get("", response_model=List[InventoryOut])
def get_inventory(
    status: str = None,
    db: Session = Depends(get_db),
    role=Depends(require_viewer()),
):
    q = db.query(Inventory)
    if status:
        q = q.filter(Inventory.inventory_status == status)
    return q.order_by(Inventory.created_at.desc()).all()


@router.get("/{inv_id}", response_model=InventoryOut)
def get_inventory_item(inv_id: int, db: Session = Depends(get_db), role=Depends(require_viewer())):
    inv = db.query(Inventory).filter(Inventory.id == inv_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    return inv


@router.patch("/{inv_id}", response_model=InventoryOut)
def update_inventory(
    inv_id: int,
    data: InventoryUpdate,
    db: Session = Depends(get_db),
    role=Depends(require_partner()),
):
    inv = db.query(Inventory).filter(Inventory.id == inv_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Inventory item not found")

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(inv, field, value)

    inv.total_invested = _calc_total_invested(inv)
    db.commit()
    db.refresh(inv)
    log_action(db, "inventory_updated", source="dashboard", entity_type="inventory", entity_id=inv_id)
    return inv


@router.post("/{inv_id}/mark-sold", response_model=InventoryOut)
def mark_sold(
    inv_id: int,
    data: InventoryMarkSold,
    db: Session = Depends(get_db),
    role=Depends(require_partner()),
):
    inv = db.query(Inventory).filter(Inventory.id == inv_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Inventory item not found")

    inv.sale_price = data.sale_price
    inv.date_sold = datetime.now(timezone.utc)
    inv.inventory_status = "sold"

    if inv.date_bought:
        delta = inv.date_sold - inv.date_bought
        inv.days_held = delta.days

    inv.total_invested = _calc_total_invested(inv)
    inv.net_profit = data.sale_price - inv.total_invested
    inv.roi_percent = (inv.net_profit / inv.total_invested * 100) if inv.total_invested > 0 else 0

    # Update listing
    listing = db.query(Listing).filter(Listing.id == inv.listing_id).first()
    if listing:
        listing.status = "sold" if data.sale_price > 0 else listing.status

    db.commit()
    db.refresh(inv)

    log_action(db, "inventory_sold", source="dashboard", entity_type="inventory", entity_id=inv_id,
               new_value={"sale_price": data.sale_price, "net_profit": inv.net_profit})

    # Fire inventory Discord alert
    try:
        import asyncio
        from app.services.discord_alerts import send_inventory_alert
        listing = db.query(Listing).filter(Listing.id == inv.listing_id).first()
        title = listing.title if listing else f"Inventory #{inv_id}"
        profit_str = f"+${inv.net_profit:,.0f}" if inv.net_profit and inv.net_profit >= 0 else f"-${abs(inv.net_profit or 0):,.0f}"
        asyncio.create_task(send_inventory_alert(
            f"**SOLD** — {title} | Sale: ${data.sale_price:,.0f} | Profit: {profit_str} | ROI: {inv.roi_percent:.1f}% | {inv.days_held} days held"
        ))
    except Exception:
        pass

    return inv
