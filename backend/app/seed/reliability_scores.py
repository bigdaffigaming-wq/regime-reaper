from sqlalchemy.orm import Session
from app.models.reliability_score import ReliabilityScore

RELIABILITY_SEED = [
    # Make-level scores (model=None = applies to all models of that make)
    {"make": "Toyota",     "model": None, "score": 18, "notes": "Highly reliable overall"},
    {"make": "Lexus",      "model": None, "score": 18, "notes": "Toyota luxury — same reliability"},
    {"make": "Honda",      "model": None, "score": 17, "notes": "Excellent long-term reliability"},
    {"make": "Acura",      "model": None, "score": 16, "notes": "Honda luxury — very reliable"},
    {"make": "Mazda",      "model": None, "score": 15, "notes": "Underrated reliability"},
    {"make": "Subaru",     "model": None, "score": 12, "notes": "Good but watch for head gaskets on older models"},
    {"make": "Ford",       "model": None, "score": 12, "notes": "Varies widely by model"},
    {"make": "Chevrolet",  "model": None, "score": 11, "notes": "Varies widely by model"},
    {"make": "GMC",        "model": None, "score": 11, "notes": "Similar to Chevrolet"},
    {"make": "Nissan",     "model": None, "score": 10, "notes": "Avoid CVT models post-2012"},
    {"make": "Infiniti",   "model": None, "score": 10, "notes": "Avoid turbo models"},
    {"make": "Hyundai",    "model": None, "score": 9,  "notes": "Improved but avoid 2011-2014 engines"},
    {"make": "Kia",        "model": None, "score": 9,  "notes": "Same engine concerns as Hyundai"},
    {"make": "Volkswagen", "model": None, "score": 7,  "notes": "High maintenance costs"},
    {"make": "BMW",        "model": None, "score": 4,  "notes": "Expensive repairs, avoid high mileage"},
    {"make": "Mercedes",   "model": None, "score": 4,  "notes": "Expensive repairs"},
    {"make": "Audi",       "model": None, "score": 3,  "notes": "High cost of ownership"},
    {"make": "Mini",       "model": None, "score": 2,  "notes": "Avoid — unreliable and expensive"},
    {"make": "Land Rover", "model": None, "score": 1,  "notes": "Auto-reject tier"},
    {"make": "Jaguar",     "model": None, "score": 1,  "notes": "Auto-reject tier"},
    # Model-level overrides — more specific than make-level
    {"make": "Toyota",  "model": "Camry",   "score": 20, "notes": "Best flip vehicle in the market"},
    {"make": "Toyota",  "model": "Corolla", "score": 20, "notes": "Extremely reliable, easy to sell"},
    {"make": "Toyota",  "model": "Prius",   "score": 17, "notes": "Watch hybrid battery — expensive if needed"},
    {"make": "Toyota",  "model": "Tacoma",  "score": 20, "notes": "High resale, always in demand"},
    {"make": "Toyota",  "model": "4Runner", "score": 20, "notes": "Premium resale, never sits"},
    {"make": "Honda",   "model": "Accord",  "score": 19, "notes": "Top flip vehicle"},
    {"make": "Honda",   "model": "Civic",   "score": 19, "notes": "Top flip vehicle"},
    {"make": "Honda",   "model": "CR-V",    "score": 18, "notes": "Strong resale"},
    {"make": "Honda",   "model": "Pilot",   "score": 16, "notes": "Watch transmission on older models"},
    {"make": "Lexus",   "model": "ES",      "score": 20, "notes": "Camry platform — bulletproof"},
    {"make": "Lexus",   "model": "RX",      "score": 19, "notes": "Highly sought after"},
    {"make": "Nissan",  "model": "Altima",  "score": 8,  "notes": "CVT failure risk — deduct if high mileage"},
    {"make": "Nissan",  "model": "Sentra",  "score": 8,  "notes": "Same CVT concern"},
    {"make": "Nissan",  "model": "Frontier","score": 14, "notes": "Old V6 engine is solid"},
    {"make": "BMW",     "model": "328i",    "score": 8,  "notes": "N52 engine acceptable, avoid N20/turbo"},
    {"make": "BMW",     "model": "550i",    "score": 2,  "notes": "N63 engine — money pit"},
    {"make": "Ford",    "model": "F-150",   "score": 14, "notes": "Strong market, 5.0 V8 preferred"},
    {"make": "Ford",    "model": "Mustang", "score": 13, "notes": "Good flip if GT/V8"},
    {"make": "Ford",    "model": "Explorer","score": 9,  "notes": "Watch transmission"},
    {"make": "Chevrolet","model": "Silverado","score": 14,"notes": "Strong demand"},
    {"make": "Chevrolet","model": "Camaro", "score": 12, "notes": "Good flip if V8"},
    {"make": "Mazda",   "model": "CX-5",    "score": 16, "notes": "Rising resale value"},
    {"make": "Mazda",   "model": "Mazda3",  "score": 16, "notes": "Underrated reliable car"},
]


def seed_reliability_scores(db: Session) -> int:
    added = 0
    for item in RELIABILITY_SEED:
        existing = (
            db.query(ReliabilityScore)
            .filter(
                ReliabilityScore.make == item["make"],
                ReliabilityScore.model == item["model"],
            )
            .first()
        )
        if not existing:
            db.add(ReliabilityScore(**item))
            added += 1
    if added:
        db.commit()
    return added
