import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.core.database import get_db
from app.core.permissions import require_partner, require_viewer
from app.models.inspection_report import InspectionReport
from app.models.listing import Listing
from app.models.analysis import Analysis

router = APIRouter(prefix="/inspections", tags=["inspections"])


class InspectionSubmit(BaseModel):
    listing_id: int
    answers: dict
    notes: Optional[str] = None


def _score_inspection(answers: dict, listing: Listing, analysis: Optional[Analysis]) -> dict:
    """
    Generate full inspection report scores from answers dict.
    Each answer is True/False (yes/no).
    """
    # Mechanical score (0-100)
    mech_items = {
        "title_ok":       (True, 15, -20),
        "cel":            (False, 0, -10),
        "abs_airbag":     (False, 0, -8),
        "trans_smooth":   (True, 20, -30),
        "overheating":    (False, 0, -40),
        "leaks":          (False, 0, -15),
        "obd_clean":      (True, 15, -10),
        "test_drive_ok":  (True, 20, -15),
        "brakes_ok":      (True, 10, -8),
    }
    mech_score = 50
    for key, (good_is_true, good_pts, bad_pts) in mech_items.items():
        val = answers.get(key)
        if val is None:
            continue
        if val == good_is_true:
            mech_score += good_pts
        else:
            mech_score += bad_pts
    mech_score = max(0, min(100, mech_score))

    # Cosmetic score (0-100)
    cosm_score = 70
    if answers.get("paint_good") is False:
        cosm_score -= 20
    if answers.get("rust") is True:
        cosm_score -= 25
    if answers.get("dents") is True:
        cosm_score -= 15
    if answers.get("glass_ok") is False:
        cosm_score -= 10
    cosm_score = max(0, min(100, cosm_score))

    # Interior score (0-100)
    int_score = 70
    if answers.get("ac_cold") is False:
        int_score -= 20
    if answers.get("interior_clean") is False:
        int_score -= 15
    if answers.get("electronics_ok") is False:
        int_score -= 10
    if answers.get("odor") is True:
        int_score -= 15
    int_score = max(0, min(100, int_score))

    # Overall score
    overall = round((mech_score * 0.5) + (cosm_score * 0.25) + (int_score * 0.25), 1)

    # Risk level
    if mech_score < 30 or answers.get("overheating") or answers.get("trans_smooth") is False:
        risk_level = "extreme"
    elif mech_score < 55:
        risk_level = "high"
    elif mech_score < 75:
        risk_level = "medium"
    else:
        risk_level = "low"

    # Profit score (uses existing analysis if available)
    profit_score = 0
    expected_profit = 0
    if analysis:
        expected_profit = analysis.expected_profit or 0
        if expected_profit >= 2000:
            profit_score = 100
        elif expected_profit >= 1500:
            profit_score = 80
        elif expected_profit >= 1000:
            profit_score = 60
        elif expected_profit >= 500:
            profit_score = 40
        else:
            profit_score = 20

    # Offer calculations
    base_price = listing.price or 0
    resale = (analysis.estimated_resale_value if analysis else 0) or base_price * 1.5
    repair_est = (analysis.estimated_repair_cost if analysis else 0) or 0

    # Adjust repair based on inspection findings
    inspection_repair_adj = 0
    if answers.get("brakes_ok") is False:
        inspection_repair_adj += 400
    if answers.get("tires_ok") is False:
        inspection_repair_adj += 325
    if answers.get("ac_cold") is False:
        inspection_repair_adj += 175
    if answers.get("leaks") is True:
        inspection_repair_adj += 400
    total_repair = repair_est + inspection_repair_adj

    recommended_offer = resale - 1500 - total_repair - 150 - 150 - 100
    recommended_offer = max(0, min(recommended_offer, base_price))

    max_offer = resale - 800 - total_repair - 150 - 150 - 100
    max_offer = max(0, min(max_offer, base_price))

    walk_away_price = resale - 500 - total_repair - 150 - 150 - 100

    return {
        "mechanical_score": mech_score,
        "cosmetic_score": cosm_score,
        "interior_score": int_score,
        "profit_score": profit_score,
        "overall_score": overall,
        "risk_level": risk_level,
        "recommended_offer": round(max(0, recommended_offer), 2),
        "max_offer": round(max(0, max_offer), 2),
        "walk_away_price": round(walk_away_price, 2),
    }


@router.post("")
def submit_inspection(data: InspectionSubmit, db: Session = Depends(get_db), role=Depends(require_partner())):
    listing = db.query(Listing).filter(Listing.id == data.listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    analysis = db.query(Analysis).filter(Analysis.listing_id == data.listing_id).first()
    scores = _score_inspection(data.answers, listing, analysis)

    report = InspectionReport(
        listing_id=data.listing_id,
        mechanical_score=scores["mechanical_score"],
        cosmetic_score=scores["cosmetic_score"],
        interior_score=scores["interior_score"],
        profit_score=scores["profit_score"],
        overall_score=scores["overall_score"],
        risk_level=scores["risk_level"],
        recommended_offer=scores["recommended_offer"],
        max_offer=scores["max_offer"],
        walk_away_price=scores["walk_away_price"],
        notes=data.notes,
        answers_json=json.dumps(data.answers),
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


@router.get("/{listing_id}")
def get_inspection(listing_id: int, db: Session = Depends(get_db), role=Depends(require_viewer())):
    report = (
        db.query(InspectionReport)
        .filter(InspectionReport.listing_id == listing_id)
        .order_by(InspectionReport.created_at.desc())
        .first()
    )
    if not report:
        raise HTTPException(status_code=404, detail="No inspection report found")
    return report
