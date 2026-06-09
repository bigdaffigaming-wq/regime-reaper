from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from sqlalchemy.sql import func
from app.core.database import Base


class ReliabilityScore(Base):
    __tablename__ = "reliability_scores"

    id = Column(Integer, primary_key=True, index=True)
    make = Column(String, nullable=False, index=True)
    model = Column(String, nullable=True, index=True)
    score = Column(Float, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
