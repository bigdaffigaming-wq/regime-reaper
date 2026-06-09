from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from app.core.database import Base


class VinReport(Base):
    __tablename__ = "vin_reports"

    id = Column(Integer, primary_key=True, index=True)
    vin = Column(String, unique=True, nullable=False, index=True)
    year = Column(String, nullable=True)
    make = Column(String, nullable=True)
    model = Column(String, nullable=True)
    trim = Column(String, nullable=True)
    engine = Column(String, nullable=True)
    drivetrain = Column(String, nullable=True)
    transmission = Column(String, nullable=True)
    fuel_type = Column(String, nullable=True)
    recalls_json = Column(Text, default="[]")
    decoded_json = Column(Text, nullable=True)
    last_checked = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
