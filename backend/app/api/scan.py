from fastapi import APIRouter, Depends, BackgroundTasks
from app.core.permissions import require_partner, require_viewer
from app.services.scanner import (
    run_scan, start_scheduler, stop_scheduler,
    update_interval, get_scan_state, scan_state,
)

router = APIRouter(prefix="/scan", tags=["scan"])


@router.get("/status")
def scan_status(role=Depends(require_viewer())):
    return get_scan_state()


@router.post("/start")
def start_scan(interval_minutes: int = 30, role=Depends(require_partner())):
    start_scheduler(interval_minutes)
    return {"status": "started", "interval_minutes": interval_minutes}


@router.post("/stop")
def stop_scan(role=Depends(require_partner())):
    stop_scheduler()
    return {"status": "stopped"}


@router.post("/now")
async def scan_now(background_tasks: BackgroundTasks, role=Depends(require_partner())):
    if scan_state["running"]:
        return {"status": "already_running"}
    background_tasks.add_task(run_scan)
    return {"status": "scan_started"}


@router.patch("/interval")
def set_interval(minutes: int, role=Depends(require_partner())):
    update_interval(minutes)
    return {"status": "updated", "interval_minutes": minutes}
