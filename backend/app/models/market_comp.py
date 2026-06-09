from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from app.core.database import Base


class MarketComp(Base):
    __tablename__ = "market_comps"

    id = Column(Integer, primary_key=True, index=True)
    make = Column(String, nullable=False, index=True)
    model = Column(String, nullable=False, index=True)
    year = Column(Integer, nullable=True)
    trim = Column(String, nullable=True)
    mileage = Column(Integer, nullable=True)
    location = Column(String, nullable=True)
    source = Column(String, nullable=False)
    listing_price = Column(Float, nullable=False)
    sold_price = Column(Float, nullable=True)
    date_found = Column(DateTime(timezone=True), nullable=True)
    url = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
