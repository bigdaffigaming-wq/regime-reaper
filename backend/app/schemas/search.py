from pydantic import BaseModel
from typing import Optional, List


class SearchParams(BaseModel):
    query: str
    location: Optional[str] = "Tampa, FL"
    radius: Optional[int] = 75
    min_price: Optional[float] = None
    max_price: Optional[float] = 2500
    min_year: Optional[int] = None
    max_mileage: Optional[int] = 200000
    sources: Optional[List[str]] = None


class FacebookSearchParams(BaseModel):
    query: str
    location: Optional[str] = "Tampa, FL"
    radius: Optional[int] = 75
    max_price: Optional[float] = 2500
    min_year: Optional[int] = None
    max_mileage: Optional[int] = 200000
