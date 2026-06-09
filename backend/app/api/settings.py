import json
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.permissions import require_partner, require_viewer
from app.models.setting import Settings
from app.schemas.settings import SettingsUpdate, SettingsOut
from app.services.audit_logger import log_action

router = APIRouter(prefix="/settings", tags=["settings"])


def _get_or_create_settings(db: Session) -> Settings:
    s = db.query(Settings).first()
    if not s:
        s = Settings()
        db.add(s)
        db.commit()
        db.refresh(s)
    return s


@router.get("", response_model=SettingsOut)
def get_settings(db: Session = Depends(get_db), role=Depends(require_viewer())):
    return _get_or_create_settings(db)


@router.patch("", response_model=SettingsOut)
def update_settings(
    data: SettingsUpdate,
    db: Session = Depends(get_db),
    role=Depends(require_partner()),
):
    s = _get_or_create_settings(db)
    old = {col.name: getattr(s, col.name) for col in s.__table__.columns}

    for field, value in data.model_dump(exclude_none=True).items():
        if field in ("enabled_sources", "target_makes", "blocked_makes") and isinstance(value, list):
            setattr(s, field, json.dumps(value))
        else:
            setattr(s, field, value)

    db.commit()
    db.refresh(s)

    log_action(db, "settings_updated", source="dashboard", entity_type="settings", entity_id=s.id,
               old_value=old, new_value=data.model_dump(exclude_none=True))
    return s
