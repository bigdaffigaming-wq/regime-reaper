from typing import Optional
from sqlalchemy.orm import Session
from app.models.repair import RepairCost
from app.core.logging import get_logger

logger = get_logger(__name__)

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

# Dealer/financing phrases — not private party cash sales
DEALER_REJECT_PHRASES = [
    "down payment",
    "down payment required",
    "financing available",
    "financing options",
    "we finance",
    "apply for financing",
    "monthly payment",
    "per month",
    "/mo",
    "buy here pay here",
    "bhph",
    "bad credit",
    "no credit",
    "in house financing",
    "dealer financing",
]

DEALER_FLAGS = [
    "florida dealer",
    "licensed dealer",
    "dealership",
    " dealer ",
    "our dealership",
    "our inventory",
    "call our",
    "visit our",
    "test drive today",
    "trade-ins welcome",
    "trade ins welcome",
    "carfax certified",
    "certified pre-owned",
]

REPAIR_KEYWORDS = {
    "check engine": ("Check Engine Light", 150, 400),
    "check engine light": ("Check Engine Light", 150, 400),
    "cel on": ("Check Engine Light", 150, 400),
    "needs brakes": ("Brake Pads + Rotors", 350, 800),
    "brakes worn": ("Brake Pads + Rotors", 350, 800),
    "bad brakes": ("Brake Pads + Rotors", 350, 800),
    "ac not working": ("AC Recharge", 100, 250),
    "ac doesn't work": ("AC Recharge", 100, 250),
    "no ac": ("AC Recharge", 100, 250),
    "hot ac": ("AC Recharge", 100, 250),
    "needs tires": ("Tires Used Set", 200, 450),
    "bald tires": ("Tires Used Set", 200, 450),
    "tires worn": ("Tires Used Set", 200, 450),
    "oil leak": ("Valve Cover Gasket", 250, 700),
    "leaking oil": ("Valve Cover Gasket", 250, 700),
    "rough idle": ("Ignition Coil/Spark Plugs", 120, 300),
    "misfires": ("Ignition Coil/Spark Plugs", 120, 300),
    "needs battery": ("Battery", 120, 220),
    "dead battery": ("Battery", 120, 220),
    "needs alternator": ("Alternator", 250, 600),
    "bad alternator": ("Alternator", 250, 600),
    "needs starter": ("Starter", 250, 600),
    "won't start": ("Starter or Battery", 120, 600),
    "electrical issue": ("Electrical Diagnosis", 200, 800),
    "electrical problem": ("Electrical Diagnosis", 200, 800),
    "salvage": ("Salvage Title Risk", 0, 0),
    "rebuilt title": ("Rebuilt Title Risk", 0, 0),
}

CONDITION_REPAIR_MAP = {
    "check engine light": 300,
    "ac not working": 175,
    "needs brakes": 400,
    "needs tires": 325,
    "oil leak": 400,
    "electrical issue": 500,
    "rough idle": 210,
}


def check_auto_reject(description: str) -> Optional[str]:
    if not description:
        return None
    lower = description.lower()

    # Hard mechanical rejects
    for phrase in AUTO_REJECT_PHRASES:
        if phrase in lower:
            return phrase

    # Dealer/financing rejects — not private party cash sales
    for phrase in DEALER_REJECT_PHRASES:
        if phrase in lower:
            return f"dealer/financing listing: '{phrase}'"

    return None


def check_dealer_flags(description: str, seller_type: Optional[str] = None) -> list[str]:
    """Returns list of dealer warning flags found in description."""
    if not description:
        return []
    flags = []
    lower = description.lower()

    # Check known dealer phrases
    for phrase in DEALER_FLAGS:
        if phrase in lower:
            flags.append(f"Dealer listing detected: '{phrase.strip()}'")
            break  # one flag is enough

    # Down payment pattern — "$X down" or "X,XXX down"
    import re
    down_pattern = re.search(r'\$[\d,]+\s*down|\d[\d,]*\s*down\b', lower)
    if down_pattern:
        flags.append(f"Down payment required: '{down_pattern.group().strip()}'")

    # Monthly payment pattern — "$X/mo" or "$X per month"
    monthly_pattern = re.search(r'\$[\d,]+\s*(?:/mo|per month)', lower)
    if monthly_pattern:
        flags.append(f"Monthly payment listing: '{monthly_pattern.group().strip()}'")

    if seller_type and "dealer" in seller_type.lower():
        flags.append("Seller type: Dealer")

    return flags


def estimate_repairs_from_description(description: str, db: Session) -> tuple[float, list[str]]:
    if not description:
        return 0.0, []

    lower = description.lower()
    found_repairs = []
    total_cost = 0.0
    seen = set()

    for keyword, (repair_name, low, high) in REPAIR_KEYWORDS.items():
        if keyword in lower and repair_name not in seen:
            avg = (low + high) / 2
            found_repairs.append(f"{repair_name} (~${avg:.0f})")
            total_cost += avg
            seen.add(repair_name)

    base_detail = _get_db_repair_avg(db, "Detail basic")
    if base_detail:
        total_cost += base_detail

    return round(total_cost, 2), found_repairs


def _get_db_repair_avg(db: Session, repair_name: str) -> Optional[float]:
    try:
        repair = db.query(RepairCost).filter(RepairCost.repair_name == repair_name).first()
        return repair.avg_cost if repair else None
    except Exception:
        return None


def get_all_repairs(db: Session):
    return db.query(RepairCost).all()
