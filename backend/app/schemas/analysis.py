from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ManualAnalysisRequest(BaseModel):
    title: str
    price: float
    mileage: Optional[int] = None
    year: Optional[int] = None
    make: Optional[str] = None
    model: Optional[str] = None
    description: Optional[str] = None
    title_status: Optional[str] = "clean"
    location: Optional[str] = None


class AnalysisOut(BaseModel):
    id: int
    listing_id: int
    deal_score: float
    verdict: str
    risk_level: str
    estimated_repair_cost: float
    estimated_cleaning_cost: float
    estimated_resale_value: float
    quick_sale_value: Optional[float]
    recommended_offer: Optional[float]
    expected_profit: float
    roi_percent: Optional[float]
    red_flags_json: str
    green_flags_json: str
    inspection_questions_json: str
    negotiation_message: Optional[str]
    llm_summary: Optional[str]
    description_intel_json: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
