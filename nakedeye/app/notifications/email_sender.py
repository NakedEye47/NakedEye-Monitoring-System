import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone

from app.config import settings


def send_email(subject: str, body_html: str) -> bool:
    if not settings.SMTP_USER or not settings.SMTP_PASS or not settings.ALERT_EMAIL_TO:
        print("[NakedEye] Email not configured — skipping alert")
        return False

    # Support multiple recipients (comma-separated)
    recipients = [r.strip() for r in settings.ALERT_EMAIL_TO.split(",") if r.strip()]

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.SMTP_USER
        msg["To"] = ", ".join(recipients)

        msg.attach(MIMEText(body_html, "html"))

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASS)
            server.sendmail(settings.SMTP_USER, recipients, msg.as_string())

        print(f"[NakedEye] Alert email sent to {', '.join(recipients)}")
        return True

    except Exception as e:
        print(f"[NakedEye] Email send failed: {e}")
        return False


def alert_down(monitor_name: str, url: str, error: str) -> bool:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    subject = f"🔴 NakedEye Alert — {monitor_name} is DOWN"
    body = f"""
    <div style="font-family:Arial,sans-serif;background:#080810;color:#e8e8f0;padding:32px;border-radius:12px;max-width:520px;margin:auto;border:1px solid rgba(124,58,237,0.3)">
      <div style="font-size:22px;font-weight:800;margin-bottom:4px;">🔴 Monitor Down</div>
      <div style="font-size:12px;color:#9090a8;margin-bottom:24px;font-family:monospace">{now}</div>
      <table style="width:100%;border-collapse:collapse;">
        <tr><td style="padding:8px 0;color:#9090a8;font-size:12px;font-family:monospace;width:120px">MONITOR</td><td style="padding:8px 0;font-weight:700;font-size:15px">{monitor_name}</td></tr>
        <tr><td style="padding:8px 0;color:#9090a8;font-size:12px;font-family:monospace">TARGET</td><td style="padding:8px 0;font-family:monospace;color:#c4a3f8">{url}</td></tr>
        <tr><td style="padding:8px 0;color:#9090a8;font-size:12px;font-family:monospace">REASON</td><td style="padding:8px 0;color:#f87171">{error}</td></tr>
      </table>
      <div style="margin-top:24px;padding:12px 16px;background:rgba(248,113,113,0.08);border:1px solid rgba(248,113,113,0.2);border-radius:8px;font-size:12px;color:#f87171;font-family:monospace">
        NakedEye will notify you again when the monitor recovers.
      </div>
    </div>
    """
    return send_email(subject, body)


def alert_recovered(monitor_name: str, url: str, downtime_seconds: float) -> bool:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    downtime_str = f"{int(downtime_seconds // 60)}m {int(downtime_seconds % 60)}s"
    subject = f"✅ NakedEye — {monitor_name} is back UP"
    body = f"""
    <div style="font-family:Arial,sans-serif;background:#080810;color:#e8e8f0;padding:32px;border-radius:12px;max-width:520px;margin:auto;border:1px solid rgba(124,58,237,0.3)">
      <div style="font-size:22px;font-weight:800;margin-bottom:4px;">✅ Monitor Recovered</div>
      <div style="font-size:12px;color:#9090a8;margin-bottom:24px;font-family:monospace">{now}</div>
      <table style="width:100%;border-collapse:collapse;">
        <tr><td style="padding:8px 0;color:#9090a8;font-size:12px;font-family:monospace;width:120px">MONITOR</td><td style="padding:8px 0;font-weight:700;font-size:15px">{monitor_name}</td></tr>
        <tr><td style="padding:8px 0;color:#9090a8;font-size:12px;font-family:monospace">TARGET</td><td style="padding:8px 0;font-family:monospace;color:#c4a3f8">{url}</td></tr>
        <tr><td style="padding:8px 0;color:#9090a8;font-size:12px;font-family:monospace">DOWNTIME</td><td style="padding:8px 0;color:#4ade80">{downtime_str}</td></tr>
      </table>
      <div style="margin-top:24px;padding:12px 16px;background:rgba(74,222,128,0.08);border:1px solid rgba(74,222,128,0.2);border-radius:8px;font-size:12px;color:#4ade80;font-family:monospace">
        Monitor is responding normally again.
      </div>
    </div>
    """
    return send_email(subject, body)
