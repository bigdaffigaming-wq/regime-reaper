import json
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.permissions import require_partner, require_viewer
from app.models.listing import Listing
from app.models.analysis import Analysis
from app.schemas.analysis import AnalysisOut, ManualAnalysisRequest
from app.services import scoring, valuation, repair_estimator, llm_analysis, discord_alerts
from app.services.audit_logger import log_action

router = APIRouter(prefix="/analysis", tags=["analysis"])


def _build_analysis(listing_data: dict, db: Session) -> dict:
    """Core analysis engine — runs scoring, valuation, and profit math."""
    price = listing_data.get("price", 0)
    make = listing_data.get("make")
    model = listing_data.get("model")
    year = listing_data.get("year")
    mileage = listing_data.get("mileage")
    description = listing_data.get("description", "")
    title_status = listing_data.get("title_status", "clean")
    seller_type = listing_data.get("seller_type")

    # Auto-reject check
    reject_reason = repair_estimator.check_auto_reject(description)

    # Valuation
    resale = valuation.estimate_resale_value(price, make, year, mileage, title_status)
    quick_sale = valuation.estimate_quick_sale_value(resale)

    # Repair estimate
    repair_cost, repair_notes = repair_estimator.estimate_repairs_from_description(description, db)
    cleaning_cost = 150.0
    title_fees = 150.0
    misc_buffer = 100.0

    # Profit math
    total_invested = price + repair_cost + cleaning_cost + title_fees + misc_buffer
    expected_profit = resale - total_invested
    roi = (expected_profit / total_invested * 100) if total_invested > 0 else 0

    # Recommended offer
    recommended_offer = resale - 1500 - repair_cost - cleaning_cost - title_fees - misc_buffer
    recommended_offer = min(recommended_offer, price)

    # Score — now passes model + db for DB-driven reliability lookup
    score_result = scoring.calculate_deal_score(
        price, resale, make, model, mileage, description, title_status, expected_profit, db
    )
    deal_score = score_result["total"]

    # Risk level
    risk_level = scoring.determine_risk_level(description, title_status, reject_reason)

    # Verdict
    verdict = scoring.determine_verdict(deal_score, expected_profit, risk_level, reject_reason)

    # Build flags
    red_flags = []
    green_flags = []

    if reject_reason:
        red_flags.append(f"AUTO-REJECT: {reject_reason}")
    if repair_notes:
        red_flags.extend(repair_notes)
    if title_status in ("salvage", "rebuilt"):
        red_flags.append(f"{title_status.title()} title")

    # Dealer/financing flags — even if not auto-rejected, warn loudly
    seller_type = listing_data.get("seller_type")
    dealer_flags = repair_estimator.check_dealer_flags(description, seller_type)
    red_flags.extend(dealer_flags)

    if make and make.lower() in ("toyota", "lexus", "honda", "acura", "mazda"):
        green_flags.append(f"Reliable make: {make}")
    if mileage and mileage < 120000:
        green_flags.append(f"Low mileage: {mileage:,}")
    if title_status == "clean":
        green_flags.append("Clean title")
    if expected_profit >= 1500:
        green_flags.append(f"Strong profit: ${expected_profit:,.0f}")
    if scoring.score_seller_motivation(description) >= 7:
        green_flags.append("Motivated seller")

    return {
        "deal_score": round(deal_score, 1),
        "verdict": verdict,
        "risk_level": risk_level,
        "estimated_repair_cost": round(repair_cost, 2),
        "estimated_cleaning_cost": cleaning_cost,
        "estimated_resale_value": round(resale, 2),
        "quick_sale_value": round(quick_sale, 2),
        "recommended_offer": round(max(recommended_offer, 0), 2),
        "expected_profit": round(expected_profit, 2),
        "roi_percent": round(roi, 1),
        "red_flags": red_flags,
        "green_flags": green_flags,
    }


@router.post("/{listing_id}", response_model=AnalysisOut)
async def analyze_listing(
    listing_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    role=Depends(require_partner()),
):
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    # Auto-enrich any listing that has a URL but no description yet
    if listing.url and not listing.description:
        try:
            detail = None
            if listing.source == "facebook":
                from app.adapters.facebook_scrapfly import FacebookScrapflyAdapter
                fb = FacebookScrapflyAdapter()
                if fb._ready():
                    detail = await fb.fetch_detail(listing.url)
            elif listing.source == "craigslist":
                from app.adapters.craigslist import CraigslistAdapter
                detail = await CraigslistAdapter().fetch_detail(listing.url)

            if detail:
                if detail.description:
                    listing.description = detail.description
                if detail.make and not listing.make:
                    listing.make = detail.make
                if detail.model and not listing.model:
                    listing.model = detail.model
                if detail.trim and not listing.trim:
                    listing.trim = detail.trim
                if detail.mileage and not listing.mileage:
                    listing.mileage = detail.mileage
                if detail.vin and not listing.vin:
                    listing.vin = detail.vin
                if detail.image_url and not listing.image_url:
                    listing.image_url = detail.image_url
                if detail.title_status and detail.title_status != "clean":
                    listing.title_status = detail.title_status
                # Merge raw_data (photos + vehicle_specs)
                import json as _json
                existing_raw = {}
                try:
                    existing_raw = _json.loads(listing.raw_data_json or "{}")
                except Exception:
                    pass
                if detail.raw_data:
                    for key in ("_all_photos", "photos", "vehicle_specs", "attrs"):
                        if detail.raw_data.get(key):
                            existing_raw[key] = detail.raw_data[key]
                listing.raw_data_json = _json.dumps(existing_raw)
                db.commit()
                db.refresh(listing)
        except Exception as e:
            from app.core.logging import get_logger
            get_logger(__name__).warning(f"Detail enrichment failed: {e}")

    result = _build_analysis(
        {
            "price": listing.price,
            "make": listing.make,
            "model": listing.model,
            "year": listing.year,
            "mileage": listing.mileage,
            "description": listing.description,
            "title_status": listing.title_status,
            "seller_type": listing.seller_type,
        },
        db,
    )

    # Save or update analysis
    existing = db.query(Analysis).filter(Analysis.listing_id == listing_id).first()
    if existing:
        for k, v in result.items():
            if k in ("red_flags", "green_flags"):
                setattr(existing, f"{k}_json", json.dumps(v))
            else:
                setattr(existing, k, v)
        analysis = existing
    else:
        analysis = Analysis(
            listing_id=listing_id,
            deal_score=result["deal_score"],
            verdict=result["verdict"],
            risk_level=result["risk_level"],
            estimated_repair_cost=result["estimated_repair_cost"],
            estimated_cleaning_cost=result["estimated_cleaning_cost"],
            estimated_resale_value=result["estimated_resale_value"],
            quick_sale_value=result["quick_sale_value"],
            recommended_offer=result["recommended_offer"],
            expected_profit=result["expected_profit"],
            roi_percent=result["roi_percent"],
            red_flags_json=json.dumps(result["red_flags"]),
            green_flags_json=json.dumps(result["green_flags"]),
            inspection_questions_json=json.dumps([]),
        )
        db.add(analysis)

    db.commit()
    db.refresh(analysis)

    log_action(db, "analysis_run", source="dashboard", entity_type="analysis", entity_id=analysis.id)

    # Run LLM + Discord alert in background
    listing_dict = {
        "id": listing.id,
        "title": listing.title,
        "price": listing.price,
        "mileage": listing.mileage,
        "location": listing.location,
        "source": listing.source,
        "url": listing.url,
        "make": listing.make,
        "year": listing.year,
        "description": listing.description,
        "title_status": listing.title_status,
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
    background_tasks.add_task(_run_llm_and_alert, db, analysis.id, listing_dict, analysis_dict, result)

    return analysis


async def _run_llm_and_alert(db: Session, analysis_id: int, listing_dict: dict, analysis_dict: dict, result: dict):
    from app.core.database import SessionLocal
    session = SessionLocal()
    try:
        llm_result = await llm_analysis.run_llm_analysis(
            listing_data=listing_dict,
            deal_score=result["deal_score"],
            verdict=result["verdict"],
            repair_estimate=result["estimated_repair_cost"],
            expected_profit=result["expected_profit"],
            red_flags=result["red_flags"],
            green_flags=result["green_flags"],
        )

        if llm_result:
            analysis = session.query(Analysis).filter(Analysis.id == analysis_id).first()
            if analysis:
                analysis.llm_summary = llm_result.get("summary")
                analysis.negotiation_message = llm_result.get("negotiation_message")
                analysis.inspection_questions_json = json.dumps(llm_result.get("inspection_questions", []))
                existing_red = json.loads(analysis.red_flags_json or "[]")
                for flag in llm_result.get("red_flags", []):
                    if not any(flag.lower()[:20] in e.lower() for e in existing_red):
                        existing_red.append(flag)
                analysis.red_flags_json = json.dumps(existing_red)
                existing_green = json.loads(analysis.green_flags_json or "[]")
                for flag in llm_result.get("green_flags", []):
                    if not any(flag.lower()[:20] in e.lower() for e in existing_green):
                        existing_green.append(flag)
                analysis.green_flags_json = json.dumps(existing_green)
                intel = llm_result.get("description_intel")
                if intel:
                    analysis.description_intel_json = json.dumps(intel)
                session.commit()

        await discord_alerts.send_deal_alert(listing_dict, analysis_dict)
    except Exception as e:
        from app.core.logging import get_logger
        get_logger(__name__).error(f"Background analysis task failed: {e}")
    finally:
        session.close()


@router.get("/{listing_id}", response_model=AnalysisOut)
def get_analysis(listing_id: int, db: Session = Depends(get_db), role=Depends(require_viewer())):
    analysis = db.query(Analysis).filter(Analysis.listing_id == listing_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return analysis


@router.post("/manual", response_model=dict)
async def analyze_manual(
    data: ManualAnalysisRequest,
    db: Session = Depends(get_db),
    role=Depends(require_viewer()),
):
    result = _build_analysis(data.model_dump(), db)
    return result
