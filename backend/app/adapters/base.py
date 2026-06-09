from abc import ABC, abstractmethod
from typing import Optional
from pydantic import BaseModel


class NormalizedListing(BaseModel):
    source: str
    external_id: Optional[str] = None
    url: Optional[str] = None
    title: str
    year: Optional[int] = None
    make: Optional[str] = None
    model: Optional[str] = None
    trim: Optional[str] = None
    price: float
    mileage: Optional[int] = None
    location: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    vin: Optional[str] = None
    seller_name: Optional[str] = None
    seller_type: Optional[str] = None
    is_sold: bool = False
    is_pending: bool = False
    raw_data: Optional[dict] = None


class SearchParams(BaseModel):
    query: str
    location: Optional[str] = "Tampa, FL"
    radius: Optional[int] = 75
    min_price: Optional[float] = None
    max_price: Optional[float] = 2500
    min_year: Optional[int] = None
    max_mileage: Optional[int] = 200000


class SourceAdapter(ABC):
    source_name: str

    @abstractmethod
    async def search(self, params: SearchParams) -> list[NormalizedListing]:
        pass

    @abstractmethod
    async def fetch_detail(self, url: str) -> Optional[NormalizedListing]:
        pass
