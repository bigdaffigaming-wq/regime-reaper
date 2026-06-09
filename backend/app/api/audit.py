from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.permissions import require_partner
from app.models.audit import AuditLog

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("")
def get_audit_logs(
    limit: int = 100,
    offset: int = 0,
    source: str = None,
    db: Session = Depends(get_db),
    role=Depends(require_partner()),
):
    q = db.query(AuditLog)
    if source:
        q = q.filter(AuditLog.source == source)
    return q.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()
