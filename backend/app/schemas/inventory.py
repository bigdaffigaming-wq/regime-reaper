from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class InventoryCreate(BaseModel):
    purchase_price: float
    repair_cost_actual: float = 0
    cleaning_cost_actual: float = 0
    title_fees: float = 150
    misc_costs: float = 100
    notes: Optional[str] = None


class InventoryUpdate(BaseModel):
    repair_cost_actual: Optional[float] = None
    cleaning_cost_actual: Optional[float] = None
    title_fees: Optional[float] = None
    misc_costs: Optional[float] = None
    listed_price: Optional[float] = None
    inventory_status: Optional[str] = None
    notes: Optional[str] = None
    date_listed: Optional[datetime] = None


class InventoryMarkSold(BaseModel):
    sale_price: float


class InventoryOut(BaseModel):
    id: int
    listing_id: int
    purchase_price: float
    repair_cost_actual: float
    cleaning_cost_actual: float
    title_fees: float
    misc_costs: float
    total_invested: float
    listed_price: Optional[float]
    sale_price: Optional[float]
    net_profit: Optional[float]
    roi_percent: Optional[float]
    date_bought: Optional[datetime]
    date_listed: Optional[datetime]
    date_sold: Optional[datetime]
    days_held: Optional[int]
    inventory_status: str
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
