import json
import asyncio
from datetime import datetime, timezone
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.logging import get_logger

logger = get_logger(__name__)

# Global scheduler instance
scheduler = AsyncIOScheduler()

# Scan state for status endpoint
scan_state = {
    "running": False,
    "enabled": False,
    "last_scan": None,
    "last_found": 0,
    "last_alerted": 0,
    "total_scans": 0,
    "next_scan": None,
    "error": None,
}


def get_scan_state() -> dict:
    job = scheduler.get_job("auto_scan")
    if job and job.next_run_time:
        scan_state["next_scan"] = job.next_run_time.isoformat()
    return scan_state


async def run_scan():
    """
    Core scan job — reads settings, searches all enabled sources,
    deduplicates, analyzes new listings, sends Discord alerts.
    """
    if scan_state["running"]:
        logger.info("Scan already running, skipping")
        return

    scan_state["running"] = True
    scan_state["error"] = None
    found_count = 0
    alert_count = 0

    db: Session = SessionLocal()
    try:
        from app.models.setting import Settings
        from app.models.listing import Listing
        from app.models.analysis import Analysis
        from app.adapters.facebook_scrapfly import FacebookScrapflyAdapter
        from app.adapters.base import SearchParams
        from app.api.analysis import _build_analysis
        from app.services.discord_alerts import send_deal_alert

        settings = db.query(Settings).first()
        if not settings:
            logger.warning("No settings found, skipping scan")
            return

        # Parse target makes and enabled sources
        try:
            target_makes = json.loads(settings.target_makes or "[]")
        except Exception:
            target_makes = []
        try:
            enabled_sources = json.loads(settings.enabled_sources or '["facebook"]')
        except Exception:
            enabled_sources = ["facebook"]

        logger.info(f"Auto-scan starting — sources: {enabled_sources}, makes: {target_makes}")

        # Build search queries — one per target make + a general sweep
        queries = list(target_makes) if target_makes else ["car"]
        queries = queries[:5]  # Cap at 5 queries per scan to save credits

        adapters = []
        if "facebook" in enabled_sources:
            fb = FacebookScrapflyAdapter()
            if fb._ready():
                adapters.append(fb)
            else:
                logger.warning("Facebook adapter not ready, skipping")
        if "craigslist" in enabled_sources:
            from app.adapters.craigslist import CraigslistAdapter
            adapters.append(CraigslistAdapter())

        if not adapters:
            logger.warning("No adapters available, skipping scan")
            return

        for query in queries:
            params = SearchParams(
                query=query,
                location=settings.default_location,
                radius=settings.radius_miles,
                max_price=settings.max_price,
                min_price=settings.min_price,
                max_mileage=settings.max_mileage,
            )

            import asyncio as _asyncio
            try:
                results_list = await _asyncio.gather(
                    *[a.search(params) for a in adapters],
                    return_exceptions=True
                )
                results = []
                for r in results_list:
                    if isinstance(r, list):
                        results.extend(r)
                logger.info(f"Scan query '{query}': {len(results)} results across {len(adapters)} sources")
            except Exception as e:
                logger.error(f"Scan search failed for '{query}': {e}")
                continue

            for nl in results:
                # Deduplicate — skip if already in DB
                if nl.external_id:
                    existing = (
                        db.query(Listing)
                        .filter(
                            Listing.external_id == nl.external_id,
                            Listing.source == nl.source,
                        )
                        .first()
                    )
                    if existing:
                        continue

                # Skip blocked makes
                try:
                    blocked = json.loads(settings.blocked_makes or "[]")
                except Exception:
                    blocked = []
                if nl.make and any(b.lower() in (nl.make or "").lower() for b in blocked):
                    continue

                # Save new listing
                listing = Listing(
                    source=nl.source,
                    external_id=nl.external_id,
                    url=nl.url,
                    title=nl.title,
                    year=nl.year,
                    make=nl.make,
                    model=nl.model,
                    trim=nl.trim,
                    price=nl.price,
                    mileage=nl.mileage,
                    location=nl.location,
                    description=nl.description,
                    image_url=nl.image_url,
                    vin=nl.vin,
                    seller_name=nl.seller_name,
                    seller_type=nl.seller_type,
                    is_sold=nl.is_sold,
                    is_pending=nl.is_pending,
                    raw_data_json=json.dumps(nl.raw_data) if nl.raw_data else None,
                    status="new",
                )
                db.add(listing)
                db.commit()
                db.refresh(listing)
                found_count += 1

                # Run analysis
                try:
                    analysis_data = _build_analysis(
                        {
                            "price": listing.price,
                            "make": listing.make,
                            "year": listing.year,
                            "mileage": listing.mileage,
                            "description": listing.description,
                            "title_status": listing.title_status,
                        },
                        db,
                    )

                    analysis = Analysis(
                        listing_id=listing.id,
                        deal_score=analysis_data["deal_score"],
                        verdict=analysis_data["verdict"],
                        risk_level=analysis_data["risk_level"],
                        estimated_repair_cost=analysis_data["estimated_repair_cost"],
                        estimated_cleaning_cost=analysis_data["estimated_cleaning_cost"],
                        estimated_resale_value=analysis_data["estimated_resale_value"],
                        quick_sale_value=analysis_data["quick_sale_value"],
                        recommended_offer=analysis_data["recommended_offer"],
                        expected_profit=analysis_data["expected_profit"],
                        roi_percent=analysis_data["roi_percent"],
                        red_flags_json=json.dumps(analysis_data["red_flags"]),
                        green_flags_json=json.dumps(analysis_data["green_flags"]),
                        inspection_questions_json=json.dumps([]),
                    )
                    db.add(analysis)
                    db.commit()

                    # Discord alert if above threshold
                    score = analysis_data["deal_score"]
                    verdict = analysis_data["verdict"]

                    if (
                        score >= settings.alert_score_threshold
                        and verdict != "WALK AWAY"
                    ):
                        listing_dict = {
                            "id": listing.id,
                            "title": listing.title,
                            "price": listing.price,
                            "mileage": listing.mileage,
                            "location": listing.location,
                            "source": listing.source,
                            "url": listing.url,
                        }
                        analysis_dict = {
                            "deal_score": analysis.deal_score,
                            "verdict": analysis.verdict,
                            "estimated_repair_cost": analysis.estimated_repair_cost,
                            "estimated_resale_value": analysis.estimated_resale_value,
                            "expected_profit": analysis.expected_profit,
                            "recommended_offer": analysis.recommended_offer,
                            "red_flags_json": analysis.red_flags_json,
                            "green_flags_json": analysis.green_flags_json,
                        }
                        alerted = await send_deal_alert(listing_dict, analysis_dict)
                        if alerted:
                            alert_count += 1

                except Exception as e:
                    logger.error(f"Analysis failed for listing {listing.id}: {e}")

            # Small delay between queries to avoid hammering
            await asyncio.sleep(2)

    except Exception as e:
        logger.error(f"Scan job error: {e}")
        scan_state["error"] = str(e)
    finally:
        db.close()
        scan_state["running"] = False
        scan_state["last_scan"] = datetime.now(timezone.utc).isoformat()
        scan_state["last_found"] = found_count
        scan_state["last_alerted"] = alert_count
        scan_state["total_scans"] += 1
        logger.info(f"Scan complete — found: {found_count}, alerted: {alert_count}")
        # Post scan summary to #scan-log
        try:
            from app.services.discord_alerts import send_scan_log
            await send_scan_log(f"Found **{found_count}** new leads | **{alert_count}** alerts sent | Total scans: {scan_state['total_scans']}")
        except Exception:
            pass


def start_scheduler(interval_minutes: int = 30):
    if scheduler.running:
        scheduler.remove_all_jobs()
    else:
        scheduler.start()

    scheduler.add_job(
        run_scan,
        trigger=IntervalTrigger(minutes=interval_minutes),
        id="auto_scan",
        replace_existing=True,
        max_instances=1,
    )
    scan_state["enabled"] = True
    logger.info(f"Auto-scan scheduled every {interval_minutes} minutes")


def stop_scheduler():
    if scheduler.running:
        scheduler.remove_all_jobs()
    scan_state["enabled"] = False
    scan_state["next_scan"] = None
    logger.info("Auto-scan stopped")


def update_interval(interval_minutes: int):
    if not scheduler.running:
        return
    scheduler.reschedule_job(
        "auto_scan",
        trigger=IntervalTrigger(minutes=interval_minutes),
    )
    logger.info(f"Scan interval updated to {interval_minutes} minutes")
