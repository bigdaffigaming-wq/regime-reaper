from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, index=True)
    listing_id = Column(Integer, ForeignKey("listings.id"), nullable=False, unique=True)
    purchase_price = Column(Float, nullable=False)
    repair_cost_actual = Column(Float, default=0)
    cleaning_cost_actual = Column(Float, default=0)
    title_fees = Column(Float, default=150)
    misc_costs = Column(Float, default=100)
    total_invested = Column(Float, nullable=False)
    listed_price = Column(Float, nullable=True)
    sale_price = Column(Float, nullable=True)
    net_profit = Column(Float, nullable=True)
    roi_percent = Column(Float, nullable=True)
    date_bought = Column(DateTime(timezone=True), nullable=True)
    date_listed = Column(DateTime(timezone=True), nullable=True)
    date_sold = Column(DateTime(timezone=True), nullable=True)
    days_held = Column(Integer, nullable=True)
    inventory_status = Column(String, default="bought", nullable=False)
    notes = Column(Text, nullable=True)
    repair_items_json = Column(Text, default="[]")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    listing = relationship("Listing", back_populates="inventory")
