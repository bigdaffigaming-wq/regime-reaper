from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class SettingsUpdate(BaseModel):
    max_price: Optional[int] = None
    min_price: Optional[int] = None
    max_mileage: Optional[int] = None
    min_year: Optional[int] = None
    max_repair_budget: Optional[int] = None
    target_profit: Optional[int] = None
    alert_score_threshold: Optional[int] = None
    default_location: Optional[str] = None
    radius_miles: Optional[int] = None
    enabled_sources: Optional[List[str]] = None
    target_makes: Optional[List[str]] = None
    blocked_makes: Optional[List[str]] = None
    scan_frequency_minutes: Optional[int] = None


class SettingsOut(BaseModel):
    id: int
    max_price: int
    min_price: int
    max_mileage: int
    min_year: int
    max_repair_budget: int
    target_profit: int
    alert_score_threshold: int
    default_location: str
    radius_miles: int
    enabled_sources: str
    target_makes: str
    blocked_makes: str
    scan_frequency_minutes: int
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
