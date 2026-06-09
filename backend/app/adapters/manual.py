from typing import Optional
from .base import SourceAdapter, NormalizedListing, SearchParams


class ManualAdapter(SourceAdapter):
    source_name = "manual"

    async def search(self, params: SearchParams) -> list[NormalizedListing]:
        # Manual intake has no search — listings are submitted individually
        return []

    async def fetch_detail(self, url: str) -> Optional[NormalizedListing]:
        # Manual intake does not fetch details from URLs
        return None

    def normalize(self, data: dict) -> NormalizedListing:
        return NormalizedListing(
            source="manual",
            external_id=data.get("external_id"),
            url=data.get("url"),
            title=data.get("title", "Unknown"),
            year=data.get("year"),
            make=data.get("make"),
            model=data.get("model"),
            trim=data.get("trim"),
            price=float(data.get("price", 0)),
            mileage=data.get("mileage"),
            location=data.get("location"),
            description=data.get("description"),
            image_url=data.get("image_url"),
            vin=data.get("vin"),
            seller_name=data.get("seller_name"),
            seller_type=data.get("seller_type"),
            raw_data=data,
        )
