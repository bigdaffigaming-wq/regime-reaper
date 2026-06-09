from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    listing_id = Column(Integer, ForeignKey("listings.id"), nullable=False, unique=True)
    deal_score = Column(Float, nullable=False)
    verdict = Column(String, nullable=False)
    risk_level = Column(String, nullable=False)
    estimated_repair_cost = Column(Float, default=0)
    estimated_cleaning_cost = Column(Float, default=150)
    estimated_resale_value = Column(Float, nullable=False)
    quick_sale_value = Column(Float, nullable=True)
    recommended_offer = Column(Float, nullable=True)
    expected_profit = Column(Float, nullable=False)
    roi_percent = Column(Float, nullable=True)
    red_flags_json = Column(Text, default="[]")
    green_flags_json = Column(Text, default="[]")
    inspection_questions_json = Column(Text, default="[]")
    negotiation_message = Column(Text, nullable=True)
    llm_summary = Column(Text, nullable=True)
    description_intel_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    listing = relationship("Listing", back_populates="analysis")
