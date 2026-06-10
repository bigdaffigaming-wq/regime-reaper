from typing import Optional
from sqlalchemy.orm import Session
from app.core.logging import get_logger

logger = get_logger(__name__)

# Addition 8 — "won't start" removed from auto-reject (battery/starter = profitable flip)
AUTO_REJECT_PHRASES = [
    "no title",
    "needs transmission",
    "transmission slipping",
    "transmission gone",
    "needs engine",
    "engine knock",
    "engine seized",
    "overheats",
    "overheating",
    "head gasket",
    "blown head gasket",
    "limp mode",
    "stalls while driving",
    "flood",
    "flood damage",
    "fire damage",
]

MOTIVATION_SIGNALS = [
    "must sell", "must go", "moving", "relocating",
    "need gone", "no space", "bought new car", "bought another",
    "grandma car", "grandpa car", "one owner", "cash today",
    "price negotiable", "obo", "make offer",
    "need cash", "divorce", "estate sale",
]

RISK_DEDUCTIONS = {
    "check engine": -3,
    "check engine light": -3,
    "cel on": -3,
    "ac not working": -3,
    "no ac": -3,
    "hot ac": -3,
    "needs brakes": -2,
    "brakes bad": -2,
    "needs tires": -3,
    "bald tires": -3,
    "oil leak": -4,
    "leaking oil": -4,
    "electrical issue": -5,
    "electrical problem": -5,
    "rough idle": -5,
    "misfires": -5,
    "salvage": -10,
    "rebuilt title": -10,
    "transmission issue": -15,
    "overheating": -15,
    "no title": -15,
    "limp mode": -15,
}

# Fallback make-level reliability — used when DB is unavailable
MAKE_RELIABILITY_FALLBACK = {
    "toyota": 18, "lexus": 18,
    "honda": 17, "acura": 16,
    "mazda": 15,
    "ford": 12, "chevrolet": 12, "gmc": 11,
    "nissan": 10, "subaru": 12,
    "infiniti": 10,
    "hyundai": 9, "kia": 9,
    "volkswagen": 7,
    "bmw": 4, "mercedes": 4, "audi": 3,
    "mini": 2, "land rover": 1, "jaguar": 1,
}


def check_auto_reject(description: str) -> Optional[str]:
    if not description:
        return None
    lower = description.lower()
    for phrase in AUTO_REJECT_PHRASES:
        if phrase in lower:
            return phrase
    return None


def get_reliability_score(make: Optional[str], model: Optional[str], db: Optional[Session] = None) -> int:
    """
    Addition 7 — DB-driven reliability lookup.
    Checks model-level first, falls back to make-level, then to hardcoded fallback.
    """
    if not make:
        return 5

    make_key = make.strip()
    model_key = model.strip() if model else None

    if db:
        try:
            from app.models.reliability_score import ReliabilityScore

            # Try model-level match first
            if model_key:
                row = (
                    db.query(ReliabilityScore)
                    .filter(
                        ReliabilityScore.make.ilike(make_key),
                        ReliabilityScore.model.ilike(model_key),
                    )
                    .first()
                )
                if row:
                    return int(row.score)

            # Fall back to make-level (model IS NULL)
            row = (
                db.query(ReliabilityScore)
                .filter(
                    ReliabilityScore.make.ilike(make_key),
                    ReliabilityScore.model == None,  # noqa: E711
                )
                .first()
            )
            if row:
                return int(row.score)
        except Exception as e:
            logger.debug(f"DB reliability lookup failed: {e}")

    return MAKE_RELIABILITY_FALLBACK.get(make_key.lower(), 5)


def score_price(asking_price: float, estimated_resale: float) -> int:
    if estimated_resale <= 0:
        return 0
    ratio = asking_price / estimated_resale
    if ratio <= 0.50:
        return 25
    elif ratio <= 0.60:
        return 22
    elif ratio <= 0.70:
        return 18
    elif ratio <= 0.80:
        return 12
    elif ratio <= 0.90:
        return 6
    return 0


def score_mileage(mileage: Optional[int]) -> int:
    if mileage is None:
        return 8
    if mileage < 100000:
        return 15
    elif mileage <= 140000:
        return 12
    elif mileage <= 180000:
        return 8
    elif mileage <= 220000:
        return 4
    return 1


def score_repair_risk(description: Optional[str], title_status: str = "clean") -> int:
    score = 15
    if not description:
        return score

    lower = description.lower()
    seen = set()
    for phrase, deduction in RISK_DEDUCTIONS.items():
        if phrase in lower and phrase not in seen:
            score += deduction
            seen.add(phrase)

    if title_status in ("salvage", "rebuilt") and "salvage" not in seen and "rebuilt title" not in seen:
        score -= 10

    return max(0, score)


def score_profit(expected_profit: float) -> int:
    if expected_profit >= 2000:
        return 15
    elif expected_profit >= 1500:
        return 12
    elif expected_profit >= 1000:
        return 9
    elif expected_profit >= 500:
        return 5
    return 0


def score_seller_motivation(description: Optional[str]) -> int:
    if not description:
        return 0
    lower = description.lower()
    signals = sum(1 for sig in MOTIVATION_SIGNALS if sig in lower)
    if signals >= 3:
        return 10
    elif signals == 2:
        return 7
    elif signals == 1:
        return 4
    return 0


def determine_risk_level(
    description: Optional[str],
    title_status: str,
    auto_reject_reason: Optional[str],
) -> str:
    if auto_reject_reason:
        return "extreme"
    repair_score = score_repair_risk(description, title_status)
    if repair_score >= 13:
        return "low"
    elif repair_score >= 8:
        return "medium"
    elif repair_score >= 3:
        return "high"
    return "extreme"


def determine_verdict(
    score: float,
    expected_profit: float,
    risk_level: str,
    auto_reject_reason: Optional[str],
) -> str:
    if auto_reject_reason or risk_level == "extreme":
        return "WALK AWAY"
    if score >= 85 and expected_profit >= 1500 and risk_level in ("low", "medium"):
        return "BUY NOW"
    elif score >= 70 and expected_profit >= 1000 and risk_level in ("low", "medium"):
        return "NEGOTIATE HARD"
    elif score >= 55 and expected_profit >= 500:
        return "MONITOR"
    return "WALK AWAY"


def calculate_deal_score(
    asking_price: float,
    estimated_resale: float,
    make: Optional[str],
    model: Optional[str],
    mileage: Optional[int],
    description: Optional[str],
    title_status: str,
    expected_profit: float,
    db: Optional[Session] = None,
) -> dict:
    # V1.2 — Apply Tampa market intel bonuses
    from app.services.tampa_market_intel import get_flip_score_bonus, get_vehicle_tier
    price_pts      = score_price(asking_price, estimated_resale)
    reliability_pts = get_reliability_score(make, model, db)
    mileage_pts    = score_mileage(mileage)
    repair_pts     = score_repair_risk(description, title_status)
    profit_pts     = score_profit(expected_profit)
    motivation_pts = score_seller_motivation(description)

    total = price_pts + reliability_pts + mileage_pts + repair_pts + profit_pts + motivation_pts

    # V1.2 — Apply Tampa market flip score bonus
    flip_bonus = get_flip_score_bonus(make or "")
    total += flip_bonus

    total = min(100, max(0, total))

    # V1.2 — Track vehicle tier
    tier_info = get_vehicle_tier(make or "", model or "", 2026)
    tier = tier_info.get("tier")

    return {
        "total": round(total, 1),
        "flip_bonus": flip_bonus,
        "tier": tier,
        "breakdown": {
            "price": price_pts,
            "reliability": reliability_pts,
            "mileage": mileage_pts,
            "repair_risk": repair_pts,
            "profit": profit_pts,
            "seller_motivation": motivation_pts,
        },
    }
