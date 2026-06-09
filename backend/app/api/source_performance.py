from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.permissions import require_viewer
from app.models.source_performance import SourcePerformance

router = APIRouter(prefix="/performance", tags=["source_performance"])


@router.get("")
def get_performance(db: Session = Depends(get_db), role=Depends(require_viewer())):
    return db.query(SourcePerformance).order_by(SourcePerformance.total_profit.desc()).all()
