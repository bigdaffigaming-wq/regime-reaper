from sqlalchemy.orm import Session
from app.models.repair import RepairCost

REPAIR_SEED = [
    # Electrical
    {"category": "Electrical", "repair_name": "Battery", "low_cost": 120, "high_cost": 220, "avg_cost": 170, "labor_hours": 0.5, "severity": "low"},
    {"category": "Electrical", "repair_name": "Alternator", "low_cost": 250, "high_cost": 600, "avg_cost": 425, "labor_hours": 2.0, "severity": "medium"},
    {"category": "Electrical", "repair_name": "Starter", "low_cost": 250, "high_cost": 600, "avg_cost": 425, "labor_hours": 2.0, "severity": "medium"},
    {"category": "Electrical", "repair_name": "Ignition Coil", "low_cost": 80, "high_cost": 180, "avg_cost": 130, "labor_hours": 1.0, "severity": "low", "notes": "Per coil"},
    {"category": "Electrical", "repair_name": "O2 Sensor", "low_cost": 150, "high_cost": 450, "avg_cost": 300, "labor_hours": 1.5, "severity": "medium"},
    {"category": "Electrical", "repair_name": "MAF Sensor", "low_cost": 100, "high_cost": 300, "avg_cost": 200, "labor_hours": 1.0, "severity": "medium"},
    {"category": "Electrical", "repair_name": "Crankshaft Sensor", "low_cost": 200, "high_cost": 600, "avg_cost": 400, "labor_hours": 2.0, "severity": "high"},
    {"category": "Electrical", "repair_name": "Camshaft Sensor", "low_cost": 150, "high_cost": 500, "avg_cost": 325, "labor_hours": 1.5, "severity": "medium"},
    {"category": "Electrical", "repair_name": "Electrical Diagnosis", "low_cost": 100, "high_cost": 300, "avg_cost": 200, "labor_hours": 1.5, "severity": "medium"},
    # Brakes
    {"category": "Brakes", "repair_name": "Brake Pads", "low_cost": 150, "high_cost": 350, "avg_cost": 250, "labor_hours": 1.5, "severity": "medium"},
    {"category": "Brakes", "repair_name": "Brake Pads + Rotors", "low_cost": 350, "high_cost": 800, "avg_cost": 575, "labor_hours": 3.0, "severity": "medium"},
    # Tires
    {"category": "Tires", "repair_name": "Tires Used Set", "low_cost": 200, "high_cost": 450, "avg_cost": 325, "labor_hours": 1.5, "severity": "medium"},
    {"category": "Tires", "repair_name": "Tires New Budget Set", "low_cost": 400, "high_cost": 750, "avg_cost": 575, "labor_hours": 1.5, "severity": "medium"},
    # Engine
    {"category": "Engine", "repair_name": "Spark Plugs", "low_cost": 120, "high_cost": 300, "avg_cost": 210, "labor_hours": 2.0, "severity": "low"},
    {"category": "Engine", "repair_name": "Valve Cover Gasket", "low_cost": 250, "high_cost": 700, "avg_cost": 475, "labor_hours": 3.0, "severity": "medium"},
    {"category": "Engine", "repair_name": "Oil Change", "low_cost": 50, "high_cost": 120, "avg_cost": 85, "labor_hours": 0.5, "severity": "low"},
    # Cooling
    {"category": "Cooling", "repair_name": "AC Recharge", "low_cost": 100, "high_cost": 250, "avg_cost": 175, "labor_hours": 1.0, "severity": "low"},
    {"category": "Cooling", "repair_name": "AC Compressor", "low_cost": 600, "high_cost": 1200, "avg_cost": 900, "labor_hours": 4.0, "severity": "high"},
    {"category": "Cooling", "repair_name": "Radiator", "low_cost": 350, "high_cost": 800, "avg_cost": 575, "labor_hours": 3.0, "severity": "high"},
    {"category": "Cooling", "repair_name": "Water Pump", "low_cost": 400, "high_cost": 1000, "avg_cost": 700, "labor_hours": 4.0, "severity": "high"},
    # Transmission
    {"category": "Transmission", "repair_name": "Transmission Service", "low_cost": 180, "high_cost": 350, "avg_cost": 265, "labor_hours": 2.0, "severity": "low"},
    {"category": "Transmission", "repair_name": "Transmission Replacement", "low_cost": 1500, "high_cost": 4000, "avg_cost": 2750, "labor_hours": 12.0, "severity": "extreme", "notes": "AUTO REJECT"},
    # Cosmetic
    {"category": "Cosmetic", "repair_name": "Detail basic", "low_cost": 100, "high_cost": 200, "avg_cost": 150, "labor_hours": 3.0, "severity": "low"},
    {"category": "Cosmetic", "repair_name": "Detail heavy", "low_cost": 200, "high_cost": 350, "avg_cost": 275, "labor_hours": 5.0, "severity": "low"},
    {"category": "Cosmetic", "repair_name": "Headlight Restoration", "low_cost": 40, "high_cost": 120, "avg_cost": 80, "labor_hours": 1.0, "severity": "low"},
]


def seed_repair_costs(db: Session):
    existing_names = {r.repair_name for r in db.query(RepairCost.repair_name).all()}
    added = 0
    for item in REPAIR_SEED:
        if item["repair_name"] not in existing_names:
            db.add(RepairCost(**item))
            added += 1
    if added:
        db.commit()
    return added
