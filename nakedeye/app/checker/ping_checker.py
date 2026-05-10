import asyncio
from datetime import datetime, timezone


async def check_ping(monitor: dict) -> dict:
    host = monitor["url"]  # For ping monitors, url field holds the hostname/IP
    timeout = monitor.get("timeout_seconds", 10)

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

        proc = await asyncio.create_subprocess_exec(
            "ping", "-c", "1", "-W", str(timeout), host,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout + 2)

        elapsed_ms = (datetime.now(timezone.utc) - start).total_seconds() * 1000

        if proc.returncode == 0:
            result["response_time_ms"] = round(elapsed_ms, 2)
        else:
            result["status"] = "down"
            result["error"] = "Host unreachable"

    except asyncio.TimeoutError:
        result["status"] = "down"
        result["error"] = "Ping timed out"
    except Exception as e:
        result["status"] = "down"
        result["error"] = str(e)

    return result
