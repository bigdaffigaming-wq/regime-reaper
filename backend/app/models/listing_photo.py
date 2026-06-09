from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class ListingPhoto(Base):
    __tablename__ = "listing_photos"

    id = Column(Integer, primary_key=True, index=True)
    listing_id = Column(Integer, ForeignKey("listings.id"), nullable=False, index=True)
    photo_url = Column(String, nullable=False)
    local_path = Column(String, nullable=True)
    photo_type = Column(String, default="listing")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
