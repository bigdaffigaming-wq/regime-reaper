from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.database import init_db, SessionLocal
from app.seed.repair_costs import seed_repair_costs
from app.seed.default_settings import seed_default_settings
from app.api import (
    health, listings, analysis, inventory,
    settings as settings_router, search, repairs, audit, scan,
    market_comps, negotiations, reliability, source_performance, inspections, contacts,
)

setup_logging()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Asset Acquisition Intelligence System",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(listings.router)
app.include_router(analysis.router)
app.include_router(inventory.router)
app.include_router(settings_router.router)
app.include_router(search.router)
app.include_router(repairs.router)
app.include_router(audit.router)
app.include_router(scan.router)
app.include_router(market_comps.router)
app.include_router(negotiations.router)
app.include_router(reliability.router)
app.include_router(source_performance.router)
app.include_router(inspections.router)
app.include_router(contacts.router)


@app.on_event("startup")
async def on_startup():
    init_db()
    db = SessionLocal()
    try:
        added = seed_repair_costs(db)
        seed_default_settings(db)
        if added:
            from app.core.logging import get_logger
            get_logger(__name__).info(f"Seeded {added} repair cost entries")

        # Seed reliability scores
        from app.seed.reliability_scores import seed_reliability_scores
        rel_added = seed_reliability_scores(db)
        if rel_added:
            from app.core.logging import get_logger
            get_logger(__name__).info(f"Seeded {rel_added} reliability score entries")

        # Auto-start scanner using saved interval from settings
        from app.services.scanner import start_scheduler
        from app.models.setting import Settings
        settings_row = db.query(Settings).first()
        interval = settings_row.scan_frequency_minutes if settings_row else 30
        start_scheduler(interval)
    finally:
        db.close()


@app.on_event("shutdown")
def on_shutdown():
    from app.services.scanner import scheduler
    if scheduler.running:
        scheduler.shutdown(wait=False)
