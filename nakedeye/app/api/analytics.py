from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from datetime import datetime, timezone
from pydantic import BaseModel
from typing import Optional, List
import httpx

from app.models.database import get_db, VisitorSession, VisitorEvent

router = APIRouter(tags=["analytics"])

class SessionInitRequest(BaseModel):
    site_url: str
    user_agent: str

class EventRequest(BaseModel):
    session_id: str
    event_type: str
    target_element: Optional[str] = None

def get_client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for", "")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else ""

async def resolve_location(ip: str) -> str:
    if not ip or ip in ("127.0.0.1", "localhost", "::1"):
        return "Local Network"
    
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(f"http://ip-api.com/json/{ip}")
            data = response.json()
            if data.get("status") == "success":
                city = data.get("city", "")
                country = data.get("country", "")
                return f"{city}, {country}".strip(", ")
    except Exception:
        pass
    
    return "Unknown Location"

@router.post("/public/analytics/session")
async def init_session(payload: SessionInitRequest, request: Request, db: AsyncSession = Depends(get_db)):
    ip = get_client_ip(request)
    location = await resolve_location(ip)
    
    session = VisitorSession(
        site_url=payload.site_url,
        ip_address=ip,
        location=location,
        user_agent=payload.user_agent,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    
    return {"session_id": session.id}

@router.post("/public/analytics/event")
async def log_event(payload: EventRequest, db: AsyncSession = Depends(get_db)):
    session = await db.scalar(select(VisitorSession).where(VisitorSession.id == payload.session_id))
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    event = VisitorEvent(
        session_id=session.id,
        event_type=payload.event_type,
        target_element=payload.target_element
    )
    db.add(event)
    
    session.last_activity_at = datetime.now(timezone.utc)
    
    await db.commit()
    return {"status": "ok"}

@router.get("/analytics/sessions")
async def get_sessions(db: AsyncSession = Depends(get_db)):
    # Fetch top 50 recent sessions ordered by started_at descending
    sessions = (await db.scalars(
        select(VisitorSession).order_by(VisitorSession.started_at.desc()).limit(50)
    )).all()
    
    results = []
    for s in sessions:
        results.append({
            "id": s.id,
            "site_url": s.site_url,
            "ip_address": s.ip_address,
            "location": s.location,
            "user_agent": s.user_agent,
            "started_at": s.started_at,
            "last_activity_at": s.last_activity_at,
            "is_active": s.is_active
        })
    return results

@router.get("/analytics/events/{session_id}")
async def get_events(session_id: str, db: AsyncSession = Depends(get_db)):
    events = (await db.scalars(
        select(VisitorEvent).where(VisitorEvent.session_id == session_id).order_by(VisitorEvent.timestamp.asc())
    )).all()
    
    return [
        {
            "id": e.id,
            "event_type": e.event_type,
            "target_element": e.target_element,
            "timestamp": e.timestamp
        }
        for e in events
    ]

@router.delete("/analytics/sessions/{session_id}")
async def delete_session(session_id: str, db: AsyncSession = Depends(get_db)):
    # Delete all events linked to this session first
    await db.execute(delete(VisitorEvent).where(VisitorEvent.session_id == session_id))
    # Delete the session itself
    result = await db.execute(delete(VisitorSession).where(VisitorSession.id == session_id))
    await db.commit()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"status": "deleted"}

