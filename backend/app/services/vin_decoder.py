import httpx
from typing import Optional
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


async def decode_vin(vin: str) -> Optional[dict]:
    if not vin or len(vin) != 17:
        return None

    url = f"{settings.NHTSA_VIN_URL}/{vin}?format=json"

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()

        results = data.get("Results", [])
        parsed = {}
        for item in results:
            var = item.get("Variable", "")
            val = item.get("Value", "")
            if val and val != "Not Applicable":
                parsed[var] = val

        return {
            "make": parsed.get("Make"),
            "model": parsed.get("Model"),
            "year": parsed.get("Model Year"),
            "trim": parsed.get("Trim"),
            "body_style": parsed.get("Body Class"),
            "engine": parsed.get("Displacement (L)"),
            "drive_type": parsed.get("Drive Type"),
            "fuel_type": parsed.get("Fuel Type - Primary"),
            "plant_country": parsed.get("Plant Country"),
            "series": parsed.get("Series"),
        }
    except Exception as e:
        logger.error(f"VIN decode failed for {vin}: {e}")
        return None
