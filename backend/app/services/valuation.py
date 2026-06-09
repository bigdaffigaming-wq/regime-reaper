from typing import Optional
from app.core.logging import get_logger

logger = get_logger(__name__)

# Rough resale multipliers by make (relative reliability premium)
MAKE_RESALE_PREMIUM = {
    "toyota": 1.15,
    "lexus": 1.15,
    "honda": 1.12,
    "acura": 1.10,
    "mazda": 1.08,
    "subaru": 1.05,
    "ford": 1.00,
    "chevrolet": 0.98,
    "gmc": 0.98,
    "nissan": 0.95,
    "infiniti": 0.95,
    "hyundai": 0.92,
    "kia": 0.92,
    "volkswagen": 0.90,
    "bmw": 0.85,
    "mercedes": 0.85,
    "audi": 0.82,
    "mini": 0.75,
    "land rover": 0.70,
    "jaguar": 0.70,
}

# Mileage depreciation factors
def _mileage_factor(mileage: Optional[int]) -> float:
    if mileage is None:
        return 0.85
    if mileage < 75000:
        return 1.05
    if mileage < 100000:
        return 1.00
    if mileage < 140000:
        return 0.90
    if mileage < 180000:
        return 0.80
    if mileage < 220000:
        return 0.70
    return 0.60


# Age depreciation factors
def _age_factor(year: Optional[int]) -> float:
    if year is None:
        return 0.85
    from datetime import datetime
    age = datetime.now().year - year
    if age <= 5:
        return 1.05
    if age <= 8:
        return 0.95
    if age <= 12:
        return 0.88
    if age <= 16:
        return 0.80
    return 0.72


def estimate_resale_value(
    price: float,
    make: Optional[str],
    year: Optional[int],
    mileage: Optional[int],
    title_status: str = "clean",
) -> float:
    """
    Estimate retail resale value from listing price and vehicle attributes.
    Uses price as a floor/anchor, then adjusts upward based on make/mileage/age.
    """
    base = price * 1.8  # assume asking is already discounted

    make_key = (make or "").lower()
    make_mult = MAKE_RESALE_PREMIUM.get(make_key, 1.0)

    mileage_mult = _mileage_factor(mileage)
    age_mult = _age_factor(year)

    resale = base * make_mult * mileage_mult * age_mult

    if title_status in ("salvage", "rebuilt"):
        resale *= 0.65

    return round(resale, 2)


def estimate_quick_sale_value(resale_value: float) -> float:
    return round(resale_value * 0.85, 2)


def estimate_wholesale_value(resale_value: float) -> float:
    return round(resale_value * 0.70, 2)
