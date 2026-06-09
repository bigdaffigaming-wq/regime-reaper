from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from app.core.database import Base


class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False)        # mechanic, detailer, insurance, tow, title, buyer, etc.
    company = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    address = Column(String, nullable=True)
    specialties = Column(Text, nullable=True)    # what they're good at
    rate = Column(String, nullable=True)         # "$80/hr", "flat $150 detail", etc.
    rating = Column(Integer, nullable=True)      # 1-5
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
