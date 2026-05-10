import asyncio
import json
from datetime import datetime, timezone


async def check_docker(monitor: dict) -> dict:
    """
    For Docker monitors, the 'url' field holds the container name or ID.
    Requires Docker socket to be mounted: /var/run/docker.sock
    """
    container = monitor["url"]

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
            "docker", "inspect", "--format",
            "{{json .State}}",
            container,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=10)

        elapsed_ms = (datetime.now(timezone.utc) - start).total_seconds() * 1000
        result["response_time_ms"] = round(elapsed_ms, 2)

        if proc.returncode != 0:
            result["status"] = "down"
            result["error"] = f"Container not found: {container}"
            return result

        state = json.loads(stdout.decode())

        if not state.get("Running", False):
            result["status"] = "down"
            exit_code = state.get("ExitCode", "?")
            result["error"] = f"Container stopped (exit code: {exit_code})"

    except asyncio.TimeoutError:
        result["status"] = "down"
        result["error"] = "Docker inspect timed out"
    except Exception as e:
        result["status"] = "down"
        result["error"] = str(e)

    return result
