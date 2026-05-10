from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
import uuid

from app.models.database import get_db, Monitor, CheckResult, Incident, AlertLog
from app.checker.scheduler import reload_monitors

router = APIRouter(prefix="/monitors", tags=["monitors"])


class MonitorCreate(BaseModel):
    name: str
    url: str
    type: str = "http"
    interval_seconds: int = 60
    timeout_seconds: int = 10
    keyword: Optional[str] = None
    response_threshold_ms: Optional[int] = None


class MonitorUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    interval_seconds: Optional[int] = None
    timeout_seconds: Optional[int] = None
    keyword: Optional[str] = None
    is_active: Optional[bool] = None
    response_threshold_ms: Optional[int] = None


@router.get("/")
async def list_monitors(db: AsyncSession = Depends(get_db)):
    monitors = (await db.scalars(select(Monitor))).all()
    return monitors


@router.post("/", status_code=201)
async def create_monitor(data: MonitorCreate, db: AsyncSession = Depends(get_db)):
    monitor = Monitor(id=str(uuid.uuid4()), **data.model_dump())
    db.add(monitor)
    await db.commit()
    await db.refresh(monitor)
    await reload_monitors()
    return monitor


@router.get("/{monitor_id}")
async def get_monitor(monitor_id: str, db: AsyncSession = Depends(get_db)):
    monitor = await db.get(Monitor, monitor_id)
    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")
    return monitor


@router.patch("/{monitor_id}")
async def update_monitor(monitor_id: str, data: MonitorUpdate, db: AsyncSession = Depends(get_db)):
    monitor = await db.get(Monitor, monitor_id)
    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(monitor, field, value)
    await db.commit()
    await reload_monitors()
    return monitor


@router.delete("/{monitor_id}", status_code=204)
async def delete_monitor(monitor_id: str, db: AsyncSession = Depends(get_db)):
    monitor = await db.get(Monitor, monitor_id)
    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")
    await db.delete(monitor)
    await db.commit()
    await reload_monitors()


@router.get("/{monitor_id}/history")
async def get_history(monitor_id: str, limit: int = 50, db: AsyncSession = Depends(get_db)):
    results = (await db.scalars(
        select(CheckResult)
        .where(CheckResult.monitor_id == monitor_id)
        .order_by(CheckResult.checked_at.desc())
        .limit(limit)
    )).all()
    return results


@router.get("/{monitor_id}/incidents")
async def get_monitor_incidents(monitor_id: str, db: AsyncSession = Depends(get_db)):
    incidents = (await db.scalars(
        select(Incident)
        .where(Incident.monitor_id == monitor_id)
        .order_by(Incident.started_at.desc())
    )).all()
    return incidents


@router.post("/{monitor_id}/pause", status_code=200)
async def pause_monitor(monitor_id: str, db: AsyncSession = Depends(get_db)):
    monitor = await db.get(Monitor, monitor_id)
    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")
    monitor.is_active = False
    await db.commit()
    await reload_monitors()
    return {"id": monitor_id, "is_active": False}


@router.post("/{monitor_id}/resume", status_code=200)
async def resume_monitor(monitor_id: str, db: AsyncSession = Depends(get_db)):
    monitor = await db.get(Monitor, monitor_id)
    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")
    monitor.is_active = True
    await db.commit()
    await reload_monitors()
    return {"id": monitor_id, "is_active": True}


@router.delete("/{monitor_id}/history", status_code=204)
async def clear_monitor_history(monitor_id: str, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import delete
    await db.execute(delete(CheckResult).where(CheckResult.monitor_id == monitor_id))
    await db.commit()


# ── GLOBAL INCIDENTS ENDPOINT ──────────────────────────────────────────────
# Separate router so it lives at /api/incidents/ (not /api/monitors/incidents)
incidents_router = APIRouter(prefix="/incidents", tags=["incidents"])


@incidents_router.get("/")
async def list_all_incidents(limit: int = 50, db: AsyncSession = Depends(get_db)):
    """
    Returns all incidents across all monitors, joined with monitor name/url.
    Sorted: ongoing first, then by started_at desc.
    """
    incidents = (await db.scalars(
        select(Incident)
        .order_by(Incident.started_at.desc())
        .limit(limit)
    )).all()

    # Enrich with monitor name + url
    result = []
    monitor_cache = {}
    for inc in incidents:
        if inc.monitor_id not in monitor_cache:
            m = await db.get(Monitor, inc.monitor_id)
            monitor_cache[inc.monitor_id] = m
        m = monitor_cache[inc.monitor_id]
        result.append({
            "id":           inc.id,
            "monitor_id":   inc.monitor_id,
            "monitor_name": m.name if m else "Deleted Monitor",
            "monitor_url":  m.url  if m else "",
            "started_at":   inc.started_at,
            "resolved_at":  inc.resolved_at,
        })

    return result

@incidents_router.delete("/", status_code=204)
async def clear_all_incidents(db: AsyncSession = Depends(get_db)):
    from sqlalchemy import delete as sql_delete
    await db.execute(sql_delete(Incident))
    await db.commit()


# ── ALERT LOG ENDPOINT ─────────────────────────────────────────────────────
alert_log_router = APIRouter(prefix="/alert-logs", tags=["alert-logs"])


@alert_log_router.get("/")
async def list_alert_logs(limit: int = 100, db: AsyncSession = Depends(get_db)):
    logs = (await db.scalars(
        select(AlertLog)
        .order_by(AlertLog.sent_at.desc())
        .limit(limit)
    )).all()
    return logs
