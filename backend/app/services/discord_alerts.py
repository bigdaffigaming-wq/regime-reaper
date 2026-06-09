import httpx
from typing import Optional
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

VERDICT_EMOJI = {
    "BUY NOW": "🟢",
    "NEGOTIATE HARD": "🟡",
    "MONITOR": "🔵",
    "WALK AWAY": "🔴",
}

RISK_EMOJI = {
    "low": "✅",
    "medium": "⚠️",
    "high": "🔶",
    "extreme": "❌",
}


def _build_alert_embed(listing: dict, analysis: dict) -> dict:
    verdict = analysis.get("verdict", "UNKNOWN")
    score = analysis.get("deal_score", 0)
    profit = analysis.get("expected_profit", 0)
    repairs = analysis.get("estimated_repair_cost", 0)
    resale = analysis.get("estimated_resale_value", 0)
    offer = analysis.get("recommended_offer")
    red_flags = analysis.get("red_flags_json", "[]")
    green_flags = analysis.get("green_flags_json", "[]")

    import json
    try:
        red = json.loads(red_flags) if isinstance(red_flags, str) else red_flags
        green = json.loads(green_flags) if isinstance(green_flags, str) else green_flags
    except Exception:
        red, green = [], []

    color = {
        "BUY NOW": 0x6AFF4F,
        "NEGOTIATE HARD": 0xFF9F1C,
        "MONITOR": 0x5865F2,
        "WALK AWAY": 0xC1121F,
    }.get(verdict, 0x0A0A0A)

    fields = [
        {"name": "Source", "value": listing.get("source", "Unknown"), "inline": True},
        {"name": "Price", "value": f"${listing.get('price', 0):,.0f}", "inline": True},
        {"name": "Mileage", "value": f"{listing.get('mileage', 'N/A'):,}" if listing.get("mileage") else "N/A", "inline": True},
        {"name": "Location", "value": listing.get("location", "Unknown"), "inline": True},
        {"name": "Score", "value": f"{score}/100", "inline": True},
        {"name": "Verdict", "value": f"{VERDICT_EMOJI.get(verdict, '')} {verdict}", "inline": True},
        {"name": "Est. Repairs", "value": f"${repairs:,.0f}", "inline": True},
        {"name": "Est. Resale", "value": f"${resale:,.0f}", "inline": True},
        {"name": "Expected Profit", "value": f"${profit:,.0f}", "inline": True},
    ]

    if offer:
        fields.append({"name": "Recommended Offer", "value": f"${offer:,.0f}", "inline": True})

    if red:
        fields.append({"name": "Red Flags", "value": "\n".join(f"• {r}" for r in red[:5]) or "None", "inline": False})
    if green:
        fields.append({"name": "Green Flags", "value": "\n".join(f"• {g}" for g in green[:5]) or "None", "inline": False})

    if listing.get("url"):
        fields.append({"name": "Link", "value": listing["url"], "inline": False})

    return {
        "title": f"☠️ REAPER DEAL ALERT — {listing.get('title', 'Unknown')}",
        "color": color,
        "fields": fields,
        "footer": {"text": "REGIME REAPER • Harvest Value. Reap Profit."},
    }


def _pick_webhook(verdict: str) -> list[str]:
    """
    Route alerts to the right channels:
    - BUY NOW  → #hot-deals + #reaper-main
    - Others   → #reaper-main only
    Always falls back to DISCORD_WEBHOOK_URL if specific channel not set.
    """
    webhooks = []
    if verdict == "BUY NOW" and settings.DISCORD_HOT_DEALS_WEBHOOK:
        webhooks.append(settings.DISCORD_HOT_DEALS_WEBHOOK)
    if settings.DISCORD_WEBHOOK_URL:
        webhooks.append(settings.DISCORD_WEBHOOK_URL)
    return webhooks


async def send_deal_alert(listing: dict, analysis: dict) -> bool:
    score = analysis.get("deal_score", 0)
    verdict = analysis.get("verdict", "")
    threshold = settings.DEFAULT_ALERT_SCORE_THRESHOLD

    if score < threshold:
        logger.info(f"Score {score} below threshold {threshold}, skipping alert")
        return False

    webhooks = _pick_webhook(verdict)
    if not webhooks:
        logger.warning("No Discord webhooks configured, skipping alert")
        return False

    embed = _build_alert_embed(listing, analysis)
    payload = {"embeds": [embed]}
    sent = False

    async with httpx.AsyncClient() as client:
        for webhook in webhooks:
            try:
                resp = await client.post(webhook, json=payload, timeout=10)
                resp.raise_for_status()
                sent = True
            except Exception as e:
                logger.error(f"Failed to send to webhook: {e}")

    if sent:
        logger.info(f"Discord alert sent — listing {listing.get('id')} verdict {verdict}")
    return sent


async def send_watchlist_alert(listing, analysis=None) -> bool:
    """Send a watchlist notification to #reaper-watchlist when a listing is saved."""
    webhook = settings.DISCORD_WATCHLIST_WEBHOOK or settings.DISCORD_WEBHOOK_URL
    if not webhook:
        return False

    score = analysis.deal_score if analysis else None
    verdict = analysis.verdict if analysis else None
    profit = analysis.expected_profit if analysis else None

    fields = [
        {"name": "Price", "value": f"${listing.price:,.0f}", "inline": True},
        {"name": "Mileage", "value": f"{listing.mileage:,} mi" if listing.mileage else "N/A", "inline": True},
        {"name": "Location", "value": listing.location or "N/A", "inline": True},
    ]
    if score is not None:
        fields.append({"name": "Score", "value": f"{score}/100", "inline": True})
    if verdict:
        fields.append({"name": "Verdict", "value": f"{VERDICT_EMOJI.get(verdict, '')} {verdict}", "inline": True})
    if profit is not None:
        fields.append({"name": "Est. Profit", "value": f"${profit:,.0f}", "inline": True})
    if listing.url:
        fields.append({"name": "Link", "value": listing.url, "inline": False})

    embed = {
        "title": f"👁 WATCHLIST — {listing.title}",
        "color": 0xFFB347,
        "fields": fields,
        "footer": {"text": "REGIME REAPER • Added to Watchlist"},
    }

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(webhook, json={"embeds": [embed]}, timeout=10)
            resp.raise_for_status()
            return True
    except Exception as e:
        logger.error(f"Watchlist webhook failed: {e}")
        return False


async def send_scan_log(message: str) -> bool:
    """Send a scan summary to the #scan-log channel."""
    if not settings.DISCORD_SCAN_LOG_WEBHOOK:
        return False
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                settings.DISCORD_SCAN_LOG_WEBHOOK,
                json={"content": f"☠️ **REAPER SCAN** — {message}"},
                timeout=10,
            )
            resp.raise_for_status()
            return True
    except Exception as e:
        logger.error(f"Scan log webhook failed: {e}")
        return False


async def send_inventory_alert(message: str) -> bool:
    """Send an inventory update to #inventory-log."""
    webhook = settings.DISCORD_INVENTORY_WEBHOOK or settings.DISCORD_WEBHOOK_URL
    if not webhook:
        return False
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(webhook, json={"content": f"📦 **INVENTORY** — {message}"}, timeout=10)
            resp.raise_for_status()
            return True
    except Exception as e:
        logger.error(f"Inventory webhook failed: {e}")
        return False
