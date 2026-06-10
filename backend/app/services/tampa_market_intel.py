"""
REGIME REAPER V1.2 — Tampa Market Intelligence Layer

S/A/B tier vehicles with profitability data and auto-alert triggers.
Integrated into scoring engine for location-specific deal prioritization.
"""

# S TIER — Highest demand, fastest sell, best profit
S_TIER_VEHICLES = {
    "Toyota_Camry": {
        "years": [2007, 2008, 2009, 2010, 2011],
        "target_buy_min": 1800,
        "target_buy_max": 3000,
        "expected_sell_min": 4500,
        "expected_sell_max": 6500,
        "expected_profit_min": 1000,
        "expected_profit_max": 2500,
        "priority_score": 100,
        "days_to_sell": 8,
        "auto_alert_price": 3000,
    },
    "Toyota_Corolla": {
        "years": [2009, 2010, 2011, 2012, 2013],
        "target_buy_min": 1500,
        "target_buy_max": 2500,
        "expected_sell_min": 4000,
        "expected_sell_max": 5500,
        "expected_profit_min": 1000,
        "expected_profit_max": 2500,
        "priority_score": 98,
        "days_to_sell": 9,
        "auto_alert_price": 2500,
    },
    "Honda_Accord": {
        "years": [2008, 2009, 2010, 2011, 2012],
        "target_buy_min": 2000,
        "target_buy_max": 3500,
        "expected_sell_min": 5000,
        "expected_sell_max": 7000,
        "expected_profit_min": 1500,
        "expected_profit_max": 3000,
        "priority_score": 96,
        "days_to_sell": 10,
        "auto_alert_price": 3000,
    },
    "Honda_Civic": {
        "years": [2008, 2009, 2010, 2011, 2012],
        "target_buy_min": 2000,
        "target_buy_max": 3000,
        "expected_sell_min": 4500,
        "expected_sell_max": 6000,
        "expected_profit_min": 1500,
        "expected_profit_max": 2500,
        "priority_score": 95,
        "days_to_sell": 9,
        "auto_alert_price": 2500,
    },
}

# A TIER — Strong demand, good profit
A_TIER_VEHICLES = {
    "Lexus_ES350": {
        "years": [2007, 2008, 2009, 2010, 2011],
        "target_buy_min": 2500,
        "target_buy_max": 4000,
        "expected_sell_min": 5500,
        "expected_sell_max": 8000,
        "expected_profit_min": 2000,
        "expected_profit_max": 4000,
        "priority_score": 94,
        "days_to_sell": 12,
        "auto_alert_price": 4000,
        "tag": "LUXURY_TOYOTA",
    },
    "Toyota_Avalon": {
        "years": [2007, 2008, 2009, 2010, 2011],
        "target_buy_min": 2500,
        "target_buy_max": 4000,
        "expected_sell_min": 5500,
        "expected_sell_max": 7500,
        "expected_profit_min": 1500,
        "expected_profit_max": 3000,
        "priority_score": 92,
        "days_to_sell": 13,
        "auto_alert_price": 3500,
    },
    "Acura_TSX": {
        "years": [2008, 2009, 2010, 2011, 2012],
        "target_buy_min": 2500,
        "target_buy_max": 4000,
        "expected_sell_min": 5500,
        "expected_sell_max": 8000,
        "expected_profit_min": 2000,
        "expected_profit_max": 3500,
        "priority_score": 91,
        "days_to_sell": 14,
        "auto_alert_price": 4000,
    },
}

# B TIER — Solid performers
B_TIER_VEHICLES = {
    "Mazda_3": {"priority_score": 85, "years": list(range(2010, 2015))},
    "Lexus_IS250": {"priority_score": 84, "years": list(range(2006, 2012))},
    "Toyota_Prius": {"priority_score": 83, "years": list(range(2008, 2014)), "note": "battery_analysis_required"},
}

# Make bonuses/penalties for flip scoring
FLIP_SCORE_MODIFIERS = {
    "Toyota": 15,
    "Honda": 15,
    "Lexus": 12,
    "Acura": 8,
    "Mazda": 5,
    "BMW": -15,
    "Audi": -15,
    "Mercedes": -15,
    "Land Rover": -20,
    "Maserati": -25,
}

# Search profiles for Tampa metro
SEARCH_PROFILES = {
    "Tampa_Core": {
        "location": "Tampa, FL",
        "radius": 50,
        "cities": ["Tampa", "St. Petersburg", "Clearwater"],
    },
    "Tampa_Extended": {
        "location": "Tampa, FL",
        "radius": 100,
        "cities": ["Tampa", "Orlando", "Lakeland", "Sarasota", "Bradenton"],
    },
    "Florida_Gold_Mine": {
        "location": "Florida",
        "radius": 250,
        "cities": [
            "Tampa", "Orlando", "Lakeland", "Ocala", "Sarasota",
            "Bradenton", "Fort Myers", "Jacksonville", "Daytona", "Gainesville"
        ],
    },
}

# Goals and targets
GOALS = {
    "annual_revenue_target": 300000,
    "weekly_flip_target_min": 3,
    "weekly_flip_target_max": 5,
    "monthly_flip_target_min": 15,
    "monthly_flip_target_max": 20,
    "minimum_profit_per_flip": 1000,
    "preferred_profit_per_flip": 1500,
    "stretch_profit_per_flip": 2500,
}


def get_vehicle_tier(make: str, model: str, year: int) -> dict:
    """Get vehicle tier and data if it exists in priority list."""
    key = f"{make}_{model}"

    if key in S_TIER_VEHICLES:
        data = S_TIER_VEHICLES[key].copy()
        data["tier"] = "S"
        return data
    if key in A_TIER_VEHICLES:
        data = A_TIER_VEHICLES[key].copy()
        data["tier"] = "A"
        return data
    if key in B_TIER_VEHICLES:
        data = B_TIER_VEHICLES[key].copy()
        data["tier"] = "B"
        return data

    return {"tier": None}


def get_flip_score_bonus(make: str) -> int:
    """Get make-based flip score modifier."""
    return FLIP_SCORE_MODIFIERS.get(make, 0)


def should_auto_alert(make: str, model: str, price: float) -> bool:
    """Check if listing meets auto-alert thresholds."""
    tier_data = get_vehicle_tier(make, model, 2026)
    if not tier_data.get("auto_alert_price"):
        return False
    return price <= tier_data["auto_alert_price"]


def estimate_profit(make: str, model: str, buy_price: float) -> dict:
    """Estimate profit range based on tier data."""
    tier_data = get_vehicle_tier(make, model, 2026)
    if not tier_data.get("tier"):
        return {}

    return {
        "expected_profit_min": tier_data.get("expected_profit_min"),
        "expected_profit_max": tier_data.get("expected_profit_max"),
        "expected_sell_min": tier_data.get("expected_sell_min"),
        "expected_sell_max": tier_data.get("expected_sell_max"),
        "days_to_sell": tier_data.get("days_to_sell"),
    }
