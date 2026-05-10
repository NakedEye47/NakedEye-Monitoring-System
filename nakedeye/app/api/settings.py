from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
import os
import re

from app.config import reload_settings
from app.notifications.email_sender import send_email
from app.notifications.sms_sender import send_sms

router = APIRouter(prefix="/settings", tags=["settings"])

ENV_PATH = os.path.join(os.path.dirname(__file__), "../../.env")


def read_env() -> dict:
    env = {}
    try:
        with open(ENV_PATH, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, val = line.partition("=")
                    env[key.strip()] = val.strip()
    except Exception:
        pass
    return env


def write_env_value(key: str, value: str):
    try:
        if os.path.exists(ENV_PATH):
            with open(ENV_PATH, "r", encoding="utf-8") as f:
                content = f.read()
        else:
            content = ""

        pattern = rf"^{re.escape(key)}=.*$"
        replacement = f"{key}={value}"

        if re.search(pattern, content, re.MULTILINE):
            content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
        else:
            content += f"\n{replacement}"

        with open(ENV_PATH, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception as e:
        print(f"[NakedEye] Failed to write .env: {e}")


@router.get("/notifications")
async def get_notification_settings():
    env = read_env()
    return {
        "smtp_host":              env.get("SMTP_HOST", "smtp.gmail.com"),
        "smtp_port":              env.get("SMTP_PORT", "587"),
        "smtp_user":              env.get("SMTP_USER", ""),
        "alert_email_to":         env.get("ALERT_EMAIL_TO", ""),
        "alert_sms_to":           env.get("ALERT_SMS_TO", ""),
        "telegram_chat_id":       env.get("TELEGRAM_CHAT_ID", ""),
        "email_configured":       bool(env.get("SMTP_USER") and env.get("SMTP_PASS") and env.get("ALERT_EMAIL_TO")),
        "sms_configured":         bool(env.get("SEMAPHORE_API_KEY") and env.get("ALERT_SMS_TO")),
        "telegram_configured":    bool(env.get("TELEGRAM_BOT_TOKEN") and env.get("TELEGRAM_CHAT_ID")),
    }


class NotificationSettings(BaseModel):
    smtp_host:          Optional[str] = None
    smtp_port:          Optional[int] = None
    smtp_user:          Optional[str] = None
    smtp_pass:          Optional[str] = None
    alert_email_to:     Optional[str] = None  # comma-separated for multiple
    semaphore_key:      Optional[str] = None
    alert_sms_to:       Optional[str] = None
    telegram_bot_token: Optional[str] = None
    telegram_chat_id:   Optional[str] = None


@router.post("/notifications")
async def save_notification_settings(data: NotificationSettings):
    mapping = {
        "SMTP_HOST":             data.smtp_host,
        "SMTP_PORT":             str(data.smtp_port) if data.smtp_port else None,
        "SMTP_USER":             data.smtp_user,
        "SMTP_PASS":             data.smtp_pass,
        "ALERT_EMAIL_TO":        data.alert_email_to,
        "SEMAPHORE_API_KEY":     data.semaphore_key,
        "ALERT_SMS_TO":          data.alert_sms_to,
        "TELEGRAM_BOT_TOKEN":    data.telegram_bot_token,
        "TELEGRAM_CHAT_ID":      data.telegram_chat_id,
    }
    for key, value in mapping.items():
        if value:
            write_env_value(key, value)
    reload_settings()
    return {"saved": True}


@router.post("/test-email")
async def test_email():
    try:
        ok = send_email(
            subject="✅ NakedEye — Test Alert",
            body_html="""
            <div style="font-family:Arial,sans-serif;background:#080810;color:#e8e8f0;padding:32px;border-radius:12px;max-width:520px;margin:auto;border:1px solid rgba(124,58,237,0.3)">
              <div style="font-size:22px;font-weight:800;margin-bottom:8px;">✅ Test Successful</div>
              <div style="font-size:14px;color:#9090a8;">Your NakedEye email alerts are working correctly.</div>
            </div>
            """
        )
        if ok:
            return {"success": True}
        return {"success": False, "error": "Email send failed — check credentials"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/test-sms")
async def test_sms():
    try:
        ok = send_sms("[NakedEye] Test alert — SMS notifications are working!")
        if ok:
            return {"success": True}
        return {"success": False, "error": "SMS send failed — check API key and top-up status"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ── GENERAL SETTINGS ──────────────────────────────────────────────────────
class GeneralSettings(BaseModel):
    default_interval:  Optional[int] = None
    default_timeout:   Optional[int] = None
    default_retries:   Optional[int] = None
    refresh_interval:  Optional[int] = None
    history_limit:     Optional[int] = None


@router.get("/general")
async def get_general_settings():
    env = read_env()
    return {
        "default_interval": int(env.get("DEFAULT_INTERVAL", 60)),
        "default_timeout":  int(env.get("DEFAULT_TIMEOUT",  10)),
        "default_retries":  int(env.get("DEFAULT_RETRIES",   1)),
        "refresh_interval": int(env.get("REFRESH_INTERVAL", 30)),
        "history_limit":    int(env.get("HISTORY_LIMIT",    60)),
    }


@router.post("/general")
async def save_general_settings(data: GeneralSettings):
    mapping = {
        "DEFAULT_INTERVAL":  str(data.default_interval)  if data.default_interval  else None,
        "DEFAULT_TIMEOUT":   str(data.default_timeout)   if data.default_timeout   else None,
        "DEFAULT_RETRIES":   str(data.default_retries)   if data.default_retries   else None,
        "REFRESH_INTERVAL":  str(data.refresh_interval)  if data.refresh_interval  else None,
        "HISTORY_LIMIT":     str(data.history_limit)     if data.history_limit     else None,
    }
    for key, value in mapping.items():
        if value:
            write_env_value(key, value)
    reload_settings()
    return {"saved": True}


# ── MAINTENANCE WINDOWS ────────────────────────────────────────────────────
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.database import get_db, MaintenanceWindow
import uuid
from datetime import datetime, timezone
from pydantic import BaseModel as PydanticBase


class MaintenanceCreate(PydanticBase):
    monitor_id:  Optional[str] = None   # None = all monitors
    label:       str
    start_time:  str   # ISO format
    end_time:    str   # ISO format


maintenance_router = APIRouter(prefix="/maintenance", tags=["maintenance"])


@maintenance_router.get("/")
async def list_maintenance(db: AsyncSession = Depends(get_db)):
    windows = (await db.scalars(
        select(MaintenanceWindow).order_by(MaintenanceWindow.start_time.desc())
    )).all()
    return windows


@maintenance_router.post("/", status_code=201)
async def create_maintenance(data: MaintenanceCreate, db: AsyncSession = Depends(get_db)):
    window = MaintenanceWindow(
        id=str(uuid.uuid4()),
        monitor_id=data.monitor_id,
        label=data.label,
        start_time=datetime.fromisoformat(data.start_time),
        end_time=datetime.fromisoformat(data.end_time),
    )
    db.add(window)
    await db.commit()
    await db.refresh(window)
    return window


@maintenance_router.delete("/{window_id}", status_code=204)
async def delete_maintenance(window_id: str, db: AsyncSession = Depends(get_db)):
    window = await db.get(MaintenanceWindow, window_id)
    if not window:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Not found")
    await db.delete(window)
    await db.commit()



@router.post("/test-telegram")
async def test_telegram():
    try:
        from app.notifications.telegram_sender import send_telegram
        ok = send_telegram("✅ <b>NakedEye Test</b>\nYour Telegram alerts are working correctly!")
        if ok:
            return {"success": True}
        return {"success": False, "error": "Telegram send failed — check bot token and chat ID"}
    except Exception as e:
        return {"success": False, "error": str(e)}
