import httpx
import ssl
import socket
from datetime import datetime, timezone


async def check_http(monitor: dict) -> dict:
    url = monitor["url"]
    timeout = monitor.get("timeout_seconds", 10)
    keyword = monitor.get("keyword")

    result = {
        "monitor_id": monitor["id"],
        "checked_at": datetime.now(timezone.utc),
        "status": "up",
        "status_code": None,
        "response_time_ms": None,
        "ssl_days_remaining": None,
        "error": None,
    }

    try:
        start = datetime.now(timezone.utc)

        async with httpx.AsyncClient(follow_redirects=True, timeout=timeout) as client:
            response = await client.get(url)

        elapsed_ms = (datetime.now(timezone.utc) - start).total_seconds() * 1000
        result["status_code"] = response.status_code
        result["response_time_ms"] = round(elapsed_ms, 2)

        if response.status_code >= 400:
            result["status"] = "down"
            result["error"] = f"HTTP {response.status_code}"

        if keyword and keyword not in response.text:
            result["status"] = "down"
            result["error"] = f"Keyword '{keyword}' not found in response"

        if url.startswith("https://"):
            result["ssl_days_remaining"] = _get_ssl_days(url)

    except httpx.TimeoutException:
        result["status"] = "down"
        result["error"] = "Connection timed out"
    except httpx.ConnectError:
        result["status"] = "down"
        result["error"] = "Could not connect"
    except Exception as e:
        result["status"] = "down"
        result["error"] = str(e)

    return result


def _get_ssl_days(url: str) -> int | None:
    try:
        hostname = url.replace("https://", "").split("/")[0].split(":")[0]
        ctx = ssl.create_default_context()
        with ctx.wrap_socket(socket.socket(), server_hostname=hostname) as s:
            s.settimeout(5)
            s.connect((hostname, 443))
            cert = s.getpeercert()
            expire_date = datetime.strptime(
                cert["notAfter"], "%b %d %H:%M:%S %Y %Z"
            ).replace(tzinfo=timezone.utc)
            return (expire_date - datetime.now(timezone.utc)).days
    except Exception:
        return None
