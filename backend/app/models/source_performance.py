from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from app.core.database import Base


class SourcePerformance(Base):
    __tablename__ = "source_performance"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String, unique=True, nullable=False, index=True)
    leads_found = Column(Integer, default=0)
    deals_reviewed = Column(Integer, default=0)
    deals_purchased = Column(Integer, default=0)
    deals_sold = Column(Integer, default=0)
    total_profit = Column(Float, default=0.0)
    average_profit = Column(Float, default=0.0)
    average_roi = Column(Float, default=0.0)
    last_updated = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
