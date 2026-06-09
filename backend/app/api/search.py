import json
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.permissions import require_partner
from app.adapters.facebook_scrapfly import FacebookScrapflyAdapter
from app.adapters.craigslist import CraigslistAdapter
from app.adapters.base import SearchParams as AdapterSearchParams
from app.models.listing import Listing
from app.schemas.search import SearchParams, FacebookSearchParams

router = APIRouter(prefix="/search", tags=["search"])

_facebook_adapter = FacebookScrapflyAdapter()
_craigslist_adapter = CraigslistAdapter()


def _save_listings(db: Session, normalized_listings: list) -> list[dict]:
    saved = []
    for nl in normalized_listings:
        existing = None
        if nl.external_id:
            existing = (
                db.query(Listing)
                .filter(Listing.external_id == nl.external_id, Listing.source == nl.source)
                .first()
            )
        if existing:
            saved.append({"id": existing.id, "new": False, **nl.model_dump(exclude={"raw_data"})})
            continue

        listing = Listing(
            source=nl.source,
            external_id=nl.external_id,
            url=nl.url,
            title=nl.title,
            year=nl.year,
            make=nl.make,
            model=nl.model,
            trim=nl.trim,
            price=nl.price,
            mileage=nl.mileage,
            location=nl.location,
            description=nl.description,
            image_url=nl.image_url,
            vin=nl.vin,
            seller_name=nl.seller_name,
            seller_type=nl.seller_type,
            is_sold=nl.is_sold,
            is_pending=nl.is_pending,
            raw_data_json=json.dumps(nl.raw_data) if nl.raw_data else None,
            status="new",
        )
        db.add(listing)
        db.commit()
        db.refresh(listing)
        saved.append({"id": listing.id, "new": True, **nl.model_dump(exclude={"raw_data"})})

    return saved


@router.post("/facebook")
async def search_facebook(
    params: FacebookSearchParams,
    db: Session = Depends(get_db),
    role=Depends(require_partner()),
):
    adapter_params = AdapterSearchParams(
        query=params.query,
        location=params.location,
        radius=params.radius,
        max_price=params.max_price,
        min_year=params.min_year,
        max_mileage=params.max_mileage,
    )
    results = await _facebook_adapter.search(adapter_params)
    saved = _save_listings(db, results)
    return {"source": "facebook", "count": len(saved), "listings": saved}


@router.post("/craigslist")
async def search_craigslist(
    params: SearchParams,
    db: Session = Depends(get_db),
    role=Depends(require_partner()),
):
    adapter_params = AdapterSearchParams(
        query=params.query,
        location=params.location,
        radius=params.radius,
        min_price=params.min_price,
        max_price=params.max_price,
        min_year=params.min_year,
        max_mileage=params.max_mileage,
    )
    results = await _craigslist_adapter.search(adapter_params)
    saved = _save_listings(db, results)
    return {"source": "craigslist", "count": len(saved), "listings": saved}


@router.post("")
async def search_all(
    params: SearchParams,
    db: Session = Depends(get_db),
    role=Depends(require_partner()),
):
    all_results = []
    sources = params.sources or ["facebook"]

    adapter_params = AdapterSearchParams(
        query=params.query,
        location=params.location,
        radius=params.radius,
        min_price=params.min_price,
        max_price=params.max_price,
        min_year=params.min_year,
        max_mileage=params.max_mileage,
    )

    import asyncio
    tasks = []
    if "facebook" in sources:
        tasks.append(_facebook_adapter.search(adapter_params))
    if "craigslist" in sources:
        tasks.append(_craigslist_adapter.search(adapter_params))

    if tasks:
        results_list = await asyncio.gather(*tasks, return_exceptions=True)
        for result in results_list:
            if isinstance(result, list):
                all_results.extend(result)

    saved = _save_listings(db, all_results)
    return {"count": len(saved), "listings": saved}
