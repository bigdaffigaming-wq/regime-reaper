from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from sqlalchemy.sql import func
from app.core.database import Base


class Settings(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    max_price = Column(Integer, default=2500)
    min_price = Column(Integer, default=1000)
    max_mileage = Column(Integer, default=200000)
    min_year = Column(Integer, default=2005)
    max_repair_budget = Column(Integer, default=500)
    target_profit = Column(Integer, default=1500)
    alert_score_threshold = Column(Integer, default=75)
    default_location = Column(String, default="Tampa, FL")
    radius_miles = Column(Integer, default=75)
    enabled_sources = Column(Text, default='["facebook","craigslist"]')
    target_makes = Column(Text, default='["Toyota","Honda","Mazda","Lexus","Acura"]')
    blocked_makes = Column(Text, default='["Land Rover","Jaguar","Mini","BMW","Mercedes","Audi"]')
    scan_frequency_minutes = Column(Integer, default=30)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
