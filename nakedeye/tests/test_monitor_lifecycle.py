import inspect
import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

try:
    from app.checker import scheduler
    from app.models.database import AlertLog, CheckResult, Incident, Monitor
except ModuleNotFoundError as exc:
    raise unittest.SkipTest(f"Project dependency is not installed: {exc.name}") from exc


class FakeSession:
    def __init__(self, monitor, scalar_values=None):
        self.monitor = monitor
        self.scalar_values = list(scalar_values or [])
        self.added = []
        self.commit_count = 0

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, model, item_id):
        if model is Monitor:
            return self.monitor
        return None

    async def scalar(self, statement):
        if self.scalar_values:
            return self.scalar_values.pop(0)
        return None

    def add(self, item):
        self.added.append(item)

    async def commit(self):
        self.commit_count += 1


def close_background_task(coro):
    if inspect.iscoroutine(coro):
        coro.close()
    return None


def make_monitor(**overrides):
    data = {
        "id": "monitor-1",
        "name": "Example",
        "type": "http",
        "url": "https://example.com",
        "timeout_seconds": 10,
        "keyword": None,
        "is_active": True,
        "response_threshold_ms": None,
        "last_status": None,
        "last_response_ms": None,
        "last_checked_at": None,
        "ssl_days_remaining": None,
    }
    data.update(overrides)
    return SimpleNamespace(**data)


class MonitorLifecycleTests(unittest.IsolatedAsyncioTestCase):
    async def test_down_check_opens_incident_and_commits_alert_logs(self):
        monitor = make_monitor()
        db = FakeSession(monitor, scalar_values=[None, None])
        result = {
            "status": "down",
            "status_code": 500,
            "response_time_ms": 123.4,
            "ssl_days_remaining": None,
            "error": "HTTP 500",
        }

        with (
            patch.object(scheduler, "AsyncSessionLocal", lambda: db),
            patch.object(scheduler, "check_http", AsyncMock(return_value=result)),
            patch.object(scheduler.asyncio, "create_task", close_background_task),
        ):
            await scheduler.run_check_for_monitor(monitor.id)

        self.assertTrue(any(isinstance(item, CheckResult) for item in db.added))
        self.assertTrue(any(isinstance(item, Incident) for item in db.added))
        down_logs = [
            item for item in db.added
            if isinstance(item, AlertLog) and item.alert_type == "down"
        ]
        self.assertEqual({log.channel for log in down_logs}, {"email", "sms", "telegram"})
        self.assertGreaterEqual(db.commit_count, 2)

    async def test_recovered_check_resolves_open_incident_and_logs_recovery(self):
        monitor = make_monitor()
        open_incident = Incident(
            monitor_id=monitor.id,
            started_at=datetime.now(timezone.utc),
        )
        db = FakeSession(monitor, scalar_values=[open_incident])
        result = {
            "status": "up",
            "status_code": 200,
            "response_time_ms": 88.0,
            "ssl_days_remaining": None,
            "error": None,
        }

        with (
            patch.object(scheduler, "AsyncSessionLocal", lambda: db),
            patch.object(scheduler, "check_http", AsyncMock(return_value=result)),
            patch.object(scheduler.asyncio, "create_task", close_background_task),
        ):
            await scheduler.run_check_for_monitor(monitor.id)

        self.assertIsNotNone(open_incident.resolved_at)
        recovery_logs = [
            item for item in db.added
            if isinstance(item, AlertLog) and item.alert_type == "recovered"
        ]
        self.assertEqual({log.channel for log in recovery_logs}, {"email", "sms", "telegram"})

    async def test_slow_check_respects_existing_cooldown_log(self):
        monitor = make_monitor(response_threshold_ms=100)
        recent_slow_log = AlertLog(monitor_id=monitor.id, channel="email", alert_type="slow")
        db = FakeSession(monitor, scalar_values=[None, None, recent_slow_log])
        result = {
            "status": "up",
            "status_code": 200,
            "response_time_ms": 250.0,
            "ssl_days_remaining": None,
            "error": None,
        }

        with (
            patch.object(scheduler, "AsyncSessionLocal", lambda: db),
            patch.object(scheduler, "check_http", AsyncMock(return_value=result)),
            patch.object(scheduler.asyncio, "create_task", close_background_task),
        ):
            await scheduler.run_check_for_monitor(monitor.id)

        slow_logs = [
            item for item in db.added
            if isinstance(item, AlertLog) and item.alert_type == "slow"
        ]
        self.assertEqual(slow_logs, [])


if __name__ == "__main__":
    unittest.main()
