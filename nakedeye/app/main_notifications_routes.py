# Add these routes to your existing main.py
# ── Notifications Settings API ────────────────────────────────────────────────

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.notifications import get_settings, save_settings, test_email, test_sms

notif_router = APIRouter(prefix="/api/notifications", tags=["notifications"])

class NotifSettings(BaseModel):
    SMTP_HOST: Optional[str] = ""
    SMTP_PORT: Optional[str] = "587"
    SMTP_USER: Optional[str] = ""
    SMTP_PASS: Optional[str] = ""
    SMTP_FROM: Optional[str] = ""
    SMTP_TO:   Optional[str] = ""
    SMS_API_KEY:    Optional[str] = ""
    SMS_SENDER:     Optional[str] = "NakedEye"
    SMS_RECIPIENTS: Optional[str] = ""
    NOTIFY_EMAIL_ENABLED: Optional[str] = "false"
    NOTIFY_SMS_ENABLED:   Optional[str] = "false"

@notif_router.get("/settings")
async def get_notif_settings():
    s = get_settings()
    # Mask password
    if s.get("SMTP_PASS"):
        s["SMTP_PASS"] = "••••••••"
    return s

@notif_router.post("/settings")
async def save_notif_settings(data: NotifSettings):
    payload = data.dict()
    # Don't overwrite password if masked value sent
    if payload.get("SMTP_PASS") == "••••••••":
        del payload["SMTP_PASS"]
    save_settings(payload)
    return {"ok": True}

@notif_router.post("/test/email")
async def test_email_route():
    result = test_email()
    return result

@notif_router.post("/test/sms")
async def test_sms_route():
    result = await test_sms()
    return result
