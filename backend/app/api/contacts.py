from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List

from app.core.database import get_db
from app.core.permissions import require_partner, require_viewer
from app.models.contact import Contact

router = APIRouter(prefix="/contacts", tags=["contacts"])

ROLES = [
    "mechanic", "detailer", "insurance", "tow", "title_agent",
    "buyer", "wholesaler", "inspector", "photographer", "other"
]


class ContactCreate(BaseModel):
    name: str
    role: str
    company: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    specialties: Optional[str] = None
    rate: Optional[str] = None
    rating: Optional[int] = None
    notes: Optional[str] = None


class ContactUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    company: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    specialties: Optional[str] = None
    rate: Optional[str] = None
    rating: Optional[int] = None
    notes: Optional[str] = None


@router.get("")
def get_contacts(role: Optional[str] = None, db: Session = Depends(get_db), role_auth=Depends(require_viewer())):
    q = db.query(Contact)
    if role:
        q = q.filter(Contact.role == role)
    return q.order_by(Contact.role, Contact.name).all()


@router.post("")
def create_contact(data: ContactCreate, db: Session = Depends(get_db), role_auth=Depends(require_partner())):
    contact = Contact(**data.model_dump())
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


@router.get("/{contact_id}")
def get_contact(contact_id: int, db: Session = Depends(get_db), role_auth=Depends(require_viewer())):
    c = db.query(Contact).filter(Contact.id == contact_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Contact not found")
    return c


@router.patch("/{contact_id}")
def update_contact(contact_id: int, data: ContactUpdate, db: Session = Depends(get_db), role_auth=Depends(require_partner())):
    c = db.query(Contact).filter(Contact.id == contact_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Contact not found")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(c, field, value)
    db.commit()
    db.refresh(c)
    return c


@router.delete("/{contact_id}")
def delete_contact(contact_id: int, db: Session = Depends(get_db), role_auth=Depends(require_partner())):
    c = db.query(Contact).filter(Contact.id == contact_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Contact not found")
    db.delete(c)
    db.commit()
    return {"deleted": True}
