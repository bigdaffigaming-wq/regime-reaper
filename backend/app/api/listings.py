import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.core.permissions import require_partner, require_viewer
from app.models.listing import Listing
from app.schemas.listing import ListingCreate, ListingUpdate, ListingOut
from app.services.audit_logger import log_action

router = APIRouter(prefix="/listings", tags=["listings"])


@router.post("", response_model=ListingOut)
def create_listing(
    data: ListingCreate,
    db: Session = Depends(get_db),
    role=Depends(require_partner()),
):
    # Deduplicate by external_id + source
    if data.external_id:
        existing = (
            db.query(Listing)
            .filter(Listing.external_id == data.external_id, Listing.source == data.source)
            .first()
        )
        if existing:
            return existing

    listing = Listing(**data.model_dump())
    db.add(listing)
    db.commit()
    db.refresh(listing)

    log_action(db, "listing_created", source="dashboard", entity_type="listing", entity_id=listing.id)
    return listing


@router.get("", response_model=List[ListingOut])
def get_listings(
    status: Optional[str] = None,
    source: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    role=Depends(require_viewer()),
):
    q = db.query(Listing)
    if status:
        q = q.filter(Listing.status == status)
    if source:
        q = q.filter(Listing.source == source)
    return q.order_by(Listing.created_at.desc()).offset(offset).limit(limit).all()


@router.get("/{listing_id}", response_model=ListingOut)
def get_listing(listing_id: int, db: Session = Depends(get_db), role=Depends(require_viewer())):
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    return listing


@router.patch("/{listing_id}", response_model=ListingOut)
def update_listing(
    listing_id: int,
    data: ListingUpdate,
    db: Session = Depends(get_db),
    role=Depends(require_partner()),
):
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    old_status = listing.status
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(listing, field, value)

    db.commit()
    db.refresh(listing)

    log_action(
        db, "listing_updated", source="dashboard",
        entity_type="listing", entity_id=listing_id,
        old_value={"status": old_status}, new_value=data.model_dump(exclude_none=True),
    )
    return listing


@router.delete("/{listing_id}")
def delete_listing(
    listing_id: int,
    db: Session = Depends(get_db),
    role=Depends(require_partner()),
):
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    db.delete(listing)
    db.commit()
    log_action(db, "listing_deleted", source="dashboard", entity_type="listing", entity_id=listing_id)
    return {"deleted": True}


@router.post("/{listing_id}/watchlist")
async def add_to_watchlist(
    listing_id: int,
    db: Session = Depends(get_db),
    role=Depends(require_partner()),
):
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    old = listing.status
    listing.status = "watchlist"
    db.commit()
    log_action(db, "listing_watchlisted", source="dashboard", entity_type="listing", entity_id=listing_id,
               old_value={"status": old}, new_value={"status": "watchlist"})

    # Discord watchlist alert
    try:
        from app.services.discord_alerts import send_watchlist_alert
        from app.models.analysis import Analysis
        analysis = db.query(Analysis).filter(Analysis.listing_id == listing_id).first()
        await send_watchlist_alert(listing, analysis)
    except Exception:
        pass

    return {"status": "watchlist"}


@router.post("/{listing_id}/enrich")
async def enrich_listing(
    listing_id: int,
    db: Session = Depends(get_db),
    role=Depends(require_partner()),
):
    """Fetch full detail page (description, specs, photos) without running analysis."""
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    if not listing.url:
        return {"enriched": False, "reason": "No URL"}

    detail = None
    try:
        if listing.source == "craigslist":
            from app.adapters.craigslist import CraigslistAdapter
            detail = await CraigslistAdapter().fetch_detail(listing.url)
        elif listing.source == "facebook":
            from app.adapters.facebook_scrapfly import FacebookScrapflyAdapter
            fb = FacebookScrapflyAdapter()
            if fb._ready():
                detail = await fb.fetch_detail(listing.url)
    except Exception as e:
        return {"enriched": False, "reason": str(e)}

    if not detail:
        return {"enriched": False, "reason": "Detail fetch returned nothing"}

    if detail.description and not listing.description:
        listing.description = detail.description
    if detail.make and not listing.make:
        listing.make = detail.make
    if detail.model and not listing.model:
        listing.model = detail.model
    if detail.mileage and not listing.mileage:
        listing.mileage = detail.mileage
    if detail.vin and not listing.vin:
        listing.vin = detail.vin

    existing_raw = {}
    try:
        existing_raw = json.loads(listing.raw_data_json or "{}")
    except Exception:
        pass
    if detail.raw_data:
        for key in ("photos", "vehicle_specs", "attrs", "_all_photos"):
            if detail.raw_data.get(key):
                existing_raw[key] = detail.raw_data[key]
    listing.raw_data_json = json.dumps(existing_raw)
    db.commit()
    db.refresh(listing)
    return {"enriched": True, "listing_id": listing_id}


@router.post("/{listing_id}/reject")
def reject_listing(
    listing_id: int,
    db: Session = Depends(get_db),
    role=Depends(require_partner()),
):
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    old = listing.status
    listing.status = "rejected"
    db.commit()
    log_action(db, "listing_rejected", source="dashboard", entity_type="listing", entity_id=listing_id,
               old_value={"status": old}, new_value={"status": "rejected"})
    return {"status": "rejected"}
