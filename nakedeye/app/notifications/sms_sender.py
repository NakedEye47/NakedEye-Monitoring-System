import httpx
from app.config import settings


def send_sms(message: str) -> bool:
    if not settings.SEMAPHORE_API_KEY or not settings.ALERT_SMS_TO:
        print("[NakedEye] SMS not configured — skipping")
        return False

    try:
        response = httpx.post(
            "https://api.semaphore.co/api/v4/messages",
            data={
                "apikey": settings.SEMAPHORE_API_KEY,
                "number": settings.ALERT_SMS_TO,
                "message": message,
                "sendername": "NakedEye",
            },
            timeout=10,
        )
        if response.status_code == 200:
            print(f"[NakedEye] SMS sent to {settings.ALERT_SMS_TO}")
            return True
        else:
            print(f"[NakedEye] SMS failed: {response.text}")
            return False
    except Exception as e:
        print(f"[NakedEye] SMS error: {e}")
        return False


def sms_alert_down(monitor_name: str, url: str, error: str) -> bool:
    msg = f"[NakedEye] ALERT: {monitor_name} is DOWN\nTarget: {url}\nReason: {error}"
    return send_sms(msg)


def sms_alert_recovered(monitor_name: str, downtime_seconds: float) -> bool:
    downtime_str = f"{int(downtime_seconds // 60)}m {int(downtime_seconds % 60)}s"
    msg = f"[NakedEye] RECOVERED: {monitor_name} is back UP after {downtime_str}"
    return send_sms(msg)
