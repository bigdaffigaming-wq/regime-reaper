import httpx
from fastapi import APIRouter
from app.core.config import settings

router = APIRouter()


@router.get("/health")
def health_check():
    return {
        "status": "online",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "scrapfly": bool(settings.SCRAPFLY_KEY),
        "groq": bool(settings.GROQ_API_KEY),
        "discord_webhook": bool(settings.DISCORD_WEBHOOK_URL),
    }


@router.get("/credits")
async def get_credits():
    """Fetch remaining Scrapfly credits from their account API."""
    if not settings.SCRAPFLY_KEY:
        return {"scrapfly": None, "error": "No Scrapfly key configured"}

    try:
        async with httpx.AsyncClient(timeout=8) as client:
            resp = await client.get(
                "https://api.scrapfly.io/account",
                params={"key": settings.SCRAPFLY_KEY},
            )
            data = resp.json()
            sub = data.get("result", {}).get("subscription", {})
            usage = sub.get("usage", {})
            return {
                "scrapfly": {
                    "plan": sub.get("period_name", "unknown"),
                    "credits_used": usage.get("scrape_api", {}).get("current", 0),
                    "credits_limit": usage.get("scrape_api", {}).get("allowed", 0),
                    "credits_remaining": (
                        usage.get("scrape_api", {}).get("allowed", 0)
                        - usage.get("scrape_api", {}).get("current", 0)
                    ),
                    "reset_at": sub.get("period_ends"),
                }
            }
    except Exception as e:
        return {"scrapfly": None, "error": str(e)}
