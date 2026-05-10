from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select
from datetime import datetime, timezone, timedelta
import asyncio

from app.models.database import AsyncSessionLocal, Monitor, CheckResult, Incident, AlertLog, MaintenanceWindow
from app.checker.http_checker import check_http
from app.checker.ping_checker import check_ping
from app.checker.docker_checker import check_docker
from app.notifications.email_sender import alert_down, alert_recovered
from app.notifications.sms_sender import sms_alert_down, sms_alert_recovered
from app.notifications.telegram_sender import telegram_alert_down, telegram_alert_recovered, telegram_alert_slow

scheduler = AsyncIOScheduler()
SLOW_ALERT_COOLDOWN_SECONDS = 3600


async def is_in_maintenance(db, monitor_id: str) -> bool:
    """Check if monitor is currently in a maintenance window."""
    now = datetime.now(timezone.utc)
    window = await db.scalar(
        select(MaintenanceWindow).where(
            (MaintenanceWindow.monitor_id == monitor_id) | (MaintenanceWindow.monitor_id.is_(None)),
            MaintenanceWindow.start_time <= now,
            MaintenanceWindow.end_time >= now,
        )
    )
    return window is not None


async def has_recent_slow_alert(db, monitor_id: str) -> bool:
    since = datetime.now(timezone.utc) - timedelta(seconds=SLOW_ALERT_COOLDOWN_SECONDS)
    recent_alert = await db.scalar(
        select(AlertLog).where(
            AlertLog.monitor_id == monitor_id,
            AlertLog.alert_type == "slow",
            AlertLog.sent_at >= since,
        )
    )
    return recent_alert is not None


async def run_check_for_monitor(monitor_id: str):
    async with AsyncSessionLocal() as db:
        monitor = await db.get(Monitor, monitor_id)
        if not monitor or not monitor.is_active:
            return

        monitor_dict = {
            "id": monitor.id,
            "url": monitor.url,
            "timeout_seconds": monitor.timeout_seconds,
            "keyword": monitor.keyword,
        }

        if monitor.type == "http":
            result = await check_http(monitor_dict)
        elif monitor.type == "ping":
            result = await check_ping(monitor_dict)
        elif monitor.type == "docker":
            result = await check_docker(monitor_dict)
        else:
            return

        # ── Normalize field name (checkers may return response_time_ms or response_ms) ──
        response_ms = result.get("response_ms") or result.get("response_time_ms")

        # ── Save check result ──
        check = CheckResult(
            monitor_id=monitor_id,
            status=result["status"],
            status_code=result.get("status_code"),
            response_ms=response_ms,
            ssl_days_remaining=result.get("ssl_days_remaining"),
            error=result.get("error"),
        )
        db.add(check)

        # ── Update monitor's cached last result ──
        monitor.last_status = result["status"]
        monitor.last_response_ms = response_ms
        monitor.last_checked_at = datetime.now(timezone.utc)
        if result.get("ssl_days_remaining") is not None:
            monitor.ssl_days_remaining = result["ssl_days_remaining"]

        # ── Handle incidents ──
        if result["status"] == "down":
            open_incident = await db.scalar(
                select(Incident).where(
                    Incident.monitor_id == monitor_id,
                    Incident.resolved_at.is_(None)
                )
            )
            if not open_incident:
                incident = Incident(
                    monitor_id=monitor_id,
                    cause=result.get("error"),
                )
                db.add(incident)
                await db.commit()

                # Skip alerts if in maintenance window
                if await is_in_maintenance(db, monitor_id):
                    print(f"[NakedEye] 🔧 {monitor.name} is DOWN but in maintenance window — skipping alert")
                else:
                    # Send alerts in background (non-blocking)
                    error_msg = result.get("error") or "Unknown error"
                    asyncio.create_task(asyncio.to_thread(
                        alert_down, monitor.name, monitor.url or "", error_msg
                    ))
                    asyncio.create_task(asyncio.to_thread(
                        sms_alert_down, monitor.name, monitor.url or "", error_msg
                    ))
                    # Log the alert
                    db.add(AlertLog(monitor_id=monitor_id, monitor_name=monitor.name, channel="email", alert_type="down", message=error_msg))
                    db.add(AlertLog(monitor_id=monitor_id, monitor_name=monitor.name, channel="sms",   alert_type="down", message=error_msg))
                    asyncio.create_task(asyncio.to_thread(
                        telegram_alert_down, monitor.name, monitor.url or "", error_msg
                    ))
                    db.add(AlertLog(monitor_id=monitor_id, monitor_name=monitor.name, channel="telegram", alert_type="down", message=error_msg))
                    await db.commit()
                    print(f"[NakedEye] 🔴 {monitor.name} is DOWN — {error_msg}")
            else:
                await db.commit()

        else:
            open_incident = await db.scalar(
                select(Incident).where(
                    Incident.monitor_id == monitor_id,
                    Incident.resolved_at.is_(None)
                )
            )
            if open_incident:
                resolved_at = datetime.now(timezone.utc)
                downtime_seconds = (resolved_at - open_incident.started_at).total_seconds()
                open_incident.resolved_at = resolved_at
                await db.commit()

                # Send recovery alerts in background (non-blocking)
                asyncio.create_task(asyncio.to_thread(
                    alert_recovered, monitor.name, monitor.url or "", downtime_seconds
                ))
                asyncio.create_task(asyncio.to_thread(
                    sms_alert_recovered, monitor.name, downtime_seconds
                ))
                # Log recovery alerts
                db.add(AlertLog(monitor_id=monitor_id, monitor_name=monitor.name, channel="email", alert_type="recovered", message=f"Downtime: {int(downtime_seconds)}s"))
                db.add(AlertLog(monitor_id=monitor_id, monitor_name=monitor.name, channel="sms",   alert_type="recovered", message=f"Downtime: {int(downtime_seconds)}s"))
                asyncio.create_task(asyncio.to_thread(
                    telegram_alert_recovered, monitor.name, downtime_seconds
                ))
                db.add(AlertLog(monitor_id=monitor_id, monitor_name=monitor.name, channel="telegram", alert_type="recovered", message=f"Downtime: {int(downtime_seconds)}s"))
                await db.commit()
                print(f"[NakedEye] ✅ {monitor.name} recovered after {int(downtime_seconds)}s")
            else:
                await db.commit()

        # ── Response threshold alert (slow response) ──
        if (result["status"] == "up"
                and monitor.response_threshold_ms
                and response_ms
                and response_ms > monitor.response_threshold_ms):
            msg = f"Slow response: {round(response_ms)}ms > threshold {monitor.response_threshold_ms}ms"
            if await is_in_maintenance(db, monitor_id):
                print(f"[NakedEye] 🔧 {monitor.name} is SLOW but in maintenance window — skipping alert")
                return
            if await has_recent_slow_alert(db, monitor_id):
                print(f"[NakedEye] {monitor.name} remains slow — alert cooldown active")
                return
            asyncio.create_task(asyncio.to_thread(
                alert_down, monitor.name, monitor.url or "", msg
            ))
            asyncio.create_task(asyncio.to_thread(
                sms_alert_down, monitor.name, monitor.url or "", msg
            ))
            asyncio.create_task(asyncio.to_thread(
                telegram_alert_slow, monitor.name, monitor.url or "", response_ms, monitor.response_threshold_ms
            ))
            async with AsyncSessionLocal() as log_db:
                log_db.add(AlertLog(monitor_id=monitor_id, monitor_name=monitor.name, channel="email", alert_type="slow", message=msg))
                log_db.add(AlertLog(monitor_id=monitor_id, monitor_name=monitor.name, channel="sms",   alert_type="slow", message=msg))
                log_db.add(AlertLog(monitor_id=monitor_id, monitor_name=monitor.name, channel="telegram", alert_type="slow", message=msg))
                await log_db.commit()
            print(f"[NakedEye] 🐌 {monitor.name} SLOW — {msg}")


async def reload_monitors():
    """Call this on startup and whenever monitors are added/updated."""
    scheduler.remove_all_jobs()

    async with AsyncSessionLocal() as db:
        monitors = (await db.scalars(select(Monitor).where(Monitor.is_active == True))).all()

    for monitor in monitors:
        scheduler.add_job(
            run_check_for_monitor,
            "interval",
            seconds=monitor.interval_seconds,
            args=[monitor.id],
            id=monitor.id,
            replace_existing=True,
            # ── Run immediately on startup too ──
            next_run_time=datetime.now(timezone.utc),
        )

    print(f"[NakedEye] Scheduler loaded {len(monitors)} monitor(s)")


def start_scheduler():
    scheduler.start()
