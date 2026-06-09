from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from sqlalchemy.sql import func
from app.core.database import Base


class RepairCost(Base):
    __tablename__ = "repair_costs"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String, nullable=False)
    repair_name = Column(String, nullable=False, unique=True)
    low_cost = Column(Float, nullable=False)
    high_cost = Column(Float, nullable=False)
    avg_cost = Column(Float, nullable=False)
    labor_hours = Column(Float, nullable=True)
    severity = Column(String, default="medium")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
