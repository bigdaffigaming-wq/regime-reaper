from pydantic import BaseModel, HttpUrl
from typing import Optional, Any
from datetime import datetime


class ListingCreate(BaseModel):
    source: str = "manual"
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
    distance_miles: Optional[float] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    vin: Optional[str] = None
    title_status: str = "clean"
    seller_name: Optional[str] = None
    seller_type: Optional[str] = None


class ListingUpdate(BaseModel):
    status: Optional[str] = None
    title_status: Optional[str] = None
    is_sold: Optional[bool] = None
    is_pending: Optional[bool] = None
    price: Optional[float] = None
    mileage: Optional[int] = None
    description: Optional[str] = None
    seller_phone: Optional[str] = None
    seller_email: Optional[str] = None
    seller_address: Optional[str] = None
    notes: Optional[str] = None


class ListingOut(BaseModel):
    id: int
    source: str
    external_id: Optional[str]
    url: Optional[str]
    title: str
    year: Optional[int]
    make: Optional[str]
    model: Optional[str]
    trim: Optional[str]
    price: float
    mileage: Optional[int]
    location: Optional[str]
    distance_miles: Optional[float]
    image_url: Optional[str]
    vin: Optional[str]
    title_status: str
    seller_name: Optional[str]
    seller_type: Optional[str]
    seller_phone: Optional[str]
    seller_email: Optional[str]
    seller_address: Optional[str]
    notes: Optional[str]
    is_sold: bool
    is_pending: bool
    status: str
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
