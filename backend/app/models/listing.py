from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Listing(Base):
    __tablename__ = "listings"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String, nullable=False)
    external_id = Column(String, nullable=True, index=True)
    url = Column(Text, nullable=True)
    title = Column(String, nullable=False)
    year = Column(Integer, nullable=True)
    make = Column(String, nullable=True)
    model = Column(String, nullable=True)
    trim = Column(String, nullable=True)
    price = Column(Float, nullable=False)
    mileage = Column(Integer, nullable=True)
    location = Column(String, nullable=True)
    distance_miles = Column(Float, nullable=True)
    description = Column(Text, nullable=True)
    image_url = Column(Text, nullable=True)
    vin = Column(String, nullable=True)
    title_status = Column(String, default="clean")
    seller_name = Column(String, nullable=True)
    seller_type = Column(String, nullable=True)
    seller_phone = Column(String, nullable=True)
    seller_email = Column(String, nullable=True)
    seller_address = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    is_sold = Column(Boolean, default=False)
    is_pending = Column(Boolean, default=False)
    raw_data_json = Column(Text, nullable=True)
    status = Column(String, default="new", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    analysis = relationship("Analysis", back_populates="listing", uselist=False)
    inventory = relationship("Inventory", back_populates="listing", uselist=False)
