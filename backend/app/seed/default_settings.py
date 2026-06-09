from sqlalchemy.orm import Session
from app.models.setting import Settings


def seed_default_settings(db: Session):
    if db.query(Settings).first():
        return
    s = Settings()
    db.add(s)
    db.commit()
