import json
from typing import Optional, Any
from sqlalchemy.orm import Session
from app.models.audit import AuditLog
from app.core.logging import get_logger

logger = get_logger(__name__)


def log_action(
    db: Session,
    action: str,
    source: str = "system",
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    old_value: Optional[Any] = None,
    new_value: Optional[Any] = None,
    user_id: Optional[int] = None,
):
    try:
        entry = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            old_value_json=json.dumps(old_value) if old_value is not None else None,
            new_value_json=json.dumps(new_value) if new_value is not None else None,
            source=source,
        )
        db.add(entry)
        db.commit()
        logger.debug(f"Audit: [{source}] {action} — {entity_type} {entity_id}")
    except Exception as e:
        logger.error(f"Audit log failed: {e}")
        db.rollback()
