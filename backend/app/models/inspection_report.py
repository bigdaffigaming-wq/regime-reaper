from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base


class InspectionReport(Base):
    __tablename__ = "inspection_reports"

    id = Column(Integer, primary_key=True, index=True)
    listing_id = Column(Integer, ForeignKey("listings.id"), nullable=False, index=True)
    mechanical_score = Column(Float, nullable=True)
    cosmetic_score = Column(Float, nullable=True)
    interior_score = Column(Float, nullable=True)
    profit_score = Column(Float, nullable=True)
    overall_score = Column(Float, nullable=True)
    recommended_offer = Column(Float, nullable=True)
    max_offer = Column(Float, nullable=True)
    walk_away_price = Column(Float, nullable=True)
    risk_level = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    answers_json = Column(Text, default="{}")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
