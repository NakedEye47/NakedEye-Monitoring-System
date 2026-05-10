import httpx
from app.config import settings


def send_telegram(message: str) -> bool:
    if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID:
        print("[NakedEye] Telegram not configured — skipping")
        return False

    try:
        response = httpx.post(
            f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage",
            json={
                "chat_id": settings.TELEGRAM_CHAT_ID,
                "text": message,
                "parse_mode": "HTML",
            },
            timeout=10,
        )
        if response.status_code == 200:
            print(f"[NakedEye] Telegram sent to {settings.TELEGRAM_CHAT_ID}")
            return True
        else:
            print(f"[NakedEye] Telegram failed: {response.text}")
            return False
    except Exception as e:
        print(f"[NakedEye] Telegram error: {e}")
        return False


def telegram_alert_down(monitor_name: str, url: str, error: str) -> bool:
    msg = (
        f"🔴 <b>Monitor Down</b>\n"
        f"<b>Monitor:</b> {monitor_name}\n"
        f"<b>Target:</b> <code>{url}</code>\n"
        f"<b>Reason:</b> {error}"
    )
    return send_telegram(msg)


def telegram_alert_recovered(monitor_name: str, downtime_seconds: float) -> bool:
    downtime_str = f"{int(downtime_seconds // 60)}m {int(downtime_seconds % 60)}s"
    msg = (
        f"✅ <b>Monitor Recovered</b>\n"
        f"<b>Monitor:</b> {monitor_name}\n"
        f"<b>Downtime:</b> {downtime_str}"
    )
    return send_telegram(msg)


def telegram_alert_slow(monitor_name: str, url: str, response_ms: float, threshold_ms: int) -> bool:
    msg = (
        f"🐌 <b>Slow Response</b>\n"
        f"<b>Monitor:</b> {monitor_name}\n"
        f"<b>Target:</b> <code>{url}</code>\n"
        f"<b>Response:</b> {round(response_ms)}ms (threshold: {threshold_ms}ms)"
    )
    return send_telegram(msg)
