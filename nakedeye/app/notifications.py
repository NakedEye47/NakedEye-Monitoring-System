import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import httpx
from dotenv import load_dotenv, set_key

load_dotenv()

ENV_FILE = ".env"

# ── Settings keys ─────────────────────────────────────────────────────────────
KEYS = [
    "SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASS",
    "SMTP_FROM", "SMTP_TO",
    "SMS_API_KEY", "SMS_SENDER", "SMS_RECIPIENTS",
    "NOTIFY_EMAIL_ENABLED", "NOTIFY_SMS_ENABLED",
]

def get_settings() -> dict:
    load_dotenv(override=True)
    return {k: os.getenv(k, "") for k in KEYS}

def save_settings(data: dict):
    for k, v in data.items():
        if k in KEYS:
            set_key(ENV_FILE, k, str(v))
            os.environ[k] = str(v)

# ── Email test ────────────────────────────────────────────────────────────────
def test_email() -> dict:
    try:
        host    = os.getenv("SMTP_HOST", "")
        port    = int(os.getenv("SMTP_PORT", 587))
        user    = os.getenv("SMTP_USER", "")
        pw      = os.getenv("SMTP_PASS", "")
        frm     = os.getenv("SMTP_FROM", user)
        to      = os.getenv("SMTP_TO", "")

        if not all([host, user, pw, to]):
            return {"ok": False, "error": "Incomplete SMTP settings"}

        msg = MIMEMultipart()
        msg["From"]    = frm
        msg["To"]      = to
        msg["Subject"] = "NakedEye — Test Email ✓"
        msg.attach(MIMEText("This is a test alert from NakedEye. Your email notifications are working!", "plain"))

        with smtplib.SMTP(host, port, timeout=10) as s:
            s.starttls()
            s.login(user, pw)
            s.sendmail(frm, to.split(","), msg.as_string())

        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}

# ── SMS test (Semaphore) ──────────────────────────────────────────────────────
async def test_sms() -> dict:
    try:
        api_key    = os.getenv("SMS_API_KEY", "")
        sender     = os.getenv("SMS_SENDER", "NakedEye")
        recipients = os.getenv("SMS_RECIPIENTS", "")

        if not all([api_key, recipients]):
            return {"ok": False, "error": "Incomplete SMS settings"}

        async with httpx.AsyncClient(timeout=10) as client:
            res = await client.post(
                "https://api.semaphore.co/api/v4/messages",
                data={
                    "apikey":      api_key,
                    "number":      recipients,
                    "message":     "NakedEye test alert — SMS notifications are working!",
                    "sendername":  sender,
                }
            )
            data = res.json()
            if res.status_code == 200:
                return {"ok": True}
            else:
                return {"ok": False, "error": str(data)}
    except Exception as e:
        return {"ok": False, "error": str(e)}

# ── Send alert (called by scheduler on down/up events) ───────────────────────
def send_email_alert(monitor_name: str, status: str, error: str = ""):
    try:
        if os.getenv("NOTIFY_EMAIL_ENABLED", "").lower() != "true":
            return
        host = os.getenv("SMTP_HOST", "")
        port = int(os.getenv("SMTP_PORT", 587))
        user = os.getenv("SMTP_USER", "")
        pw   = os.getenv("SMTP_PASS", "")
        frm  = os.getenv("SMTP_FROM", user)
        to   = os.getenv("SMTP_TO", "")
        if not all([host, user, pw, to]):
            return
        icon    = "🔴" if status == "down" else "🟢"
        subject = f"{icon} NakedEye — {monitor_name} is {status.upper()}"
        body    = f"{monitor_name} is now {status.upper()}."
        if error:
            body += f"\n\nError: {error}"
        msg = MIMEMultipart()
        msg["From"]    = frm
        msg["To"]      = to
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        with smtplib.SMTP(host, port, timeout=10) as s:
            s.starttls()
            s.login(user, pw)
            s.sendmail(frm, to.split(","), msg.as_string())
    except Exception:
        pass

async def send_sms_alert(monitor_name: str, status: str, error: str = ""):
    try:
        if os.getenv("NOTIFY_SMS_ENABLED", "").lower() != "true":
            return
        api_key    = os.getenv("SMS_API_KEY", "")
        sender     = os.getenv("SMS_SENDER", "NakedEye")
        recipients = os.getenv("SMS_RECIPIENTS", "")
        if not all([api_key, recipients]):
            return
        icon = "🔴" if status == "down" else "🟢"
        msg  = f"{icon} {monitor_name} is {status.upper()}."
        if error:
            msg += f" Error: {error[:80]}"
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(
                "https://api.semaphore.co/api/v4/messages",
                data={"apikey": api_key, "number": recipients, "message": msg, "sendername": sender}
            )
    except Exception:
        pass
