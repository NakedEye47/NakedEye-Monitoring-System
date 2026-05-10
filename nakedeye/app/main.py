from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse, Response
from starlette.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
from datetime import datetime, timezone
import hmac
import hashlib
import os
import time
from urllib.parse import parse_qs

from app.config import settings
from app.models.database import init_db, AsyncSessionLocal, Monitor, Incident
from app.checker.scheduler import start_scheduler, reload_monitors
from app.api.monitors import router as monitors_router, incidents_router, alert_log_router
from app.api.social import router as social_router
from app.api.settings import router as settings_router, maintenance_router
from app.api.jobs import router as jobs_router
from app.api.analytics import router as analytics_router
from sqlalchemy import select


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    start_scheduler()
    await reload_monitors()
    yield


app = FastAPI(
    title="NakedEye",
    description="Self-hosted uptime monitoring system",
    version="1.0.0",
    lifespan=lifespan,
)

# Allow CORS so the portfolio site can send tracking data
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

login_failures: dict[str, list[float]] = {}


def _csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for", "")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else ""


def _client_is_trusted(request: Request) -> bool:
    trusted_clients = set(_csv(settings.TRUSTED_CLIENTS))
    client_host = _client_ip(request)
    return client_host in trusted_clients


def _configured_api_key() -> str:
    if settings.API_KEY:
        return settings.API_KEY
    if settings.SECRET_KEY and settings.SECRET_KEY != "change-me":
        return settings.SECRET_KEY
    return ""


def _auth_password() -> str:
    return settings.ADMIN_PASSWORD or _configured_api_key()


def _sign_session(username: str) -> str:
    secret = _configured_api_key() or "change-me"
    sig = hmac.new(secret.encode(), username.encode(), hashlib.sha256).hexdigest()
    return f"{username}.{sig}"


def _valid_session(value: str) -> bool:
    if not value or "." not in value:
        return False
    username, _, sig = value.partition(".")
    if username != settings.ADMIN_USERNAME:
        return False
    expected = _sign_session(username).partition(".")[2]
    return hmac.compare_digest(sig, expected)


def _is_public_path(path: str) -> bool:
    return (
        path in {"/login", "/logout", "/health", "/status", "/manifest.json", "/sw.js", "/favicon.svg"}
        or path.startswith("/api/public/")
        or path.startswith("/api/jobs/email-open/")
    )


def _is_static_asset(path: str) -> bool:
    return path.startswith("/static/") and not path.endswith("/index.html")


def _is_authenticated(request: Request) -> bool:
    if _valid_session(request.cookies.get("nakedeye_session", "")):
        return True
    api_key = _configured_api_key()
    provided_key = request.headers.get("x-api-key", "")
    return bool(api_key and provided_key == api_key)


def _login_locked(client_ip: str) -> bool:
    now = time.time()
    window_start = now - settings.LOGIN_LOCKOUT_SECONDS
    failures = [item for item in login_failures.get(client_ip, []) if item >= window_start]
    login_failures[client_ip] = failures
    return len(failures) >= settings.LOGIN_MAX_ATTEMPTS


def _record_login_failure(client_ip: str):
    now = time.time()
    login_failures.setdefault(client_ip, []).append(now)


def _clear_login_failures(client_ip: str):
    login_failures.pop(client_ip, None)


@app.middleware("http")
async def reject_large_requests(request: Request, call_next):
    content_length = request.headers.get("content-length")
    try:
        if content_length and int(content_length) > settings.MAX_REQUEST_BYTES:
            return JSONResponse(status_code=413, content={"detail": "Request too large"})
    except ValueError:
        return JSONResponse(status_code=400, content={"detail": "Invalid Content-Length"})
    return await call_next(request)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(), payment=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data: https:; "
        "connect-src 'self'; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self'"
    )
    if settings.SESSION_COOKIE_SECURE:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


@app.middleware("http")
async def require_dashboard_login(request: Request, call_next):
    path = request.url.path
    if _is_public_path(path) or _is_static_asset(path):
        return await call_next(request)
    if path == "/" or path.startswith("/api"):
        if not _is_authenticated(request):
            if path.startswith("/api"):
                return JSONResponse(status_code=401, content={"detail": "Login required"})
            return RedirectResponse("/login", status_code=303)
    return await call_next(request)


@app.middleware("http")
async def protect_remote_api_writes(request: Request, call_next):
    if (
        request.url.path.startswith("/api")
        and request.method in {"POST", "PUT", "PATCH", "DELETE"}
        and not _is_public_path(request.url.path)
        and not _client_is_trusted(request)
        and not _is_authenticated(request)
    ):
        api_key = _configured_api_key()
        provided_key = request.headers.get("x-api-key", "")
        if not api_key or provided_key != api_key:
            return JSONResponse(
                status_code=403,
                content={"detail": "API key required for remote write access"},
            )
    return await call_next(request)


app.add_middleware(
    CORSMiddleware,
    allow_origins=_csv(settings.ALLOWED_ORIGINS),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

allowed_hosts = _csv(settings.ALLOWED_HOSTS)
if allowed_hosts and allowed_hosts != ["*"]:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)

app.include_router(monitors_router, prefix="/api")
app.include_router(incidents_router, prefix="/api")
app.include_router(alert_log_router, prefix="/api")
app.include_router(social_router, prefix="/api")
app.include_router(settings_router, prefix="/api")
app.include_router(maintenance_router, prefix="/api")
app.include_router(jobs_router, prefix="/api")
app.include_router(analytics_router, prefix="/api")

# Serve dashboard
static_path = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_path), name="static")

@app.get("/")
async def dashboard():
    return FileResponse(os.path.join(static_path, "index.html"))


@app.get("/login")
async def login_page():
    return FileResponse(os.path.join(static_path, "login.html"))


@app.post("/login")
async def login(request: Request):
    client_ip = _client_ip(request)
    if _login_locked(client_ip):
        return RedirectResponse("/login?locked=1", status_code=303)
    form = parse_qs((await request.body()).decode())
    username = (form.get("username") or [""])[0]
    password = (form.get("password") or [""])[0]
    if (
        hmac.compare_digest(username, settings.ADMIN_USERNAME)
        and hmac.compare_digest(password, _auth_password())
    ):
        _clear_login_failures(client_ip)
        response = RedirectResponse("/", status_code=303)
        response.set_cookie(
            "nakedeye_session",
            _sign_session(username),
            httponly=True,
            samesite="lax",
            secure=settings.SESSION_COOKIE_SECURE,
            max_age=60 * 60 * 12,
        )
        return response
    _record_login_failure(client_ip)
    response = RedirectResponse("/login?error=1", status_code=303)
    return response


@app.get("/logout")
async def logout():
    response = RedirectResponse("/login", status_code=303)
    response.delete_cookie("nakedeye_session")
    return response


@app.get("/status")
async def public_status_page():
    return FileResponse(os.path.join(static_path, "public-status.html"))


@app.get("/manifest.json")
async def manifest():
    return FileResponse(os.path.join(static_path, "manifest.json"))


@app.get("/sw.js")
async def service_worker():
    return FileResponse(os.path.join(static_path, "sw.js"))


@app.get("/favicon.svg")
async def favicon():
    return FileResponse(os.path.join(static_path, "favicon.svg"))


@app.get("/api/auth/me")
async def auth_me():
    return {"authenticated": True, "username": settings.ADMIN_USERNAME}


@app.get("/api/public/status")
async def public_status():
    async with AsyncSessionLocal() as db:
        monitors = (await db.scalars(select(Monitor))).all()
        incidents = (await db.scalars(
            select(Incident).where(Incident.resolved_at.is_(None)).order_by(Incident.started_at.desc())
        )).all()
        services = []
        for monitor in monitors:
            status = monitor.last_status or "unknown"
            services.append({
                "name": monitor.name,
                "status": status,
                "last_checked_at": monitor.last_checked_at,
                "response_ms": monitor.last_response_ms,
            })
        overall = "operational"
        if any(service["status"] == "down" for service in services):
            overall = "degraded"
        return {
            "overall": overall,
            "updated_at": datetime.now(timezone.utc),
            "services": services,
            "active_incidents": len(incidents),
        }

@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/tracker.js")
async def serve_tracker():
    """Serve tracker.js with CORS headers so it works cross-origin on any device."""
    tracker_path = os.path.join(static_path, "tracker.js")
    with open(tracker_path, "r") as f:
        content = f.read()
    return Response(
        content=content,
        media_type="application/javascript",
        headers={
            "Access-Control-Allow-Origin": "*",
            "Cache-Control": "no-cache",
        },
    )
