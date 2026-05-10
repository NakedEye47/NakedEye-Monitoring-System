from sqlalchemy import Column, String, Integer, Boolean, Float, DateTime, Text, ForeignKey, text
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from datetime import datetime, timezone
import uuid

from app.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class Monitor(Base):
    __tablename__ = "monitors"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    type = Column(String, nullable=False, default="http")
    url = Column(String, nullable=True)
    interval_seconds = Column(Integer, default=60)
    timeout_seconds = Column(Integer, default=10)
    keyword = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # ── Alert thresholds ──
    response_threshold_ms = Column(Integer, nullable=True)  # alert if response > this value

    # ── Cached last check result (updated after every check) ──
    last_status = Column(String, nullable=True)           # "up" or "down"
    last_response_ms = Column(Float, nullable=True)       # response time in ms
    last_checked_at = Column(DateTime(timezone=True), nullable=True)
    ssl_days_remaining = Column(Integer, nullable=True)

    checks = relationship("CheckResult", back_populates="monitor", cascade="all, delete")
    incidents = relationship("Incident", back_populates="monitor", cascade="all, delete")


class CheckResult(Base):
    __tablename__ = "check_results"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    monitor_id = Column(String, ForeignKey("monitors.id"), nullable=False)
    checked_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    status = Column(String, nullable=False)
    status_code = Column(Integer, nullable=True)
    response_ms = Column(Float, nullable=True)       # renamed from response_time_ms
    ssl_days_remaining = Column(Integer, nullable=True)
    error = Column(Text, nullable=True)

    monitor = relationship("Monitor", back_populates="checks")


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    monitor_id = Column(String, ForeignKey("monitors.id"), nullable=False)
    started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    cause = Column(Text, nullable=True)
    alert_sent = Column(Boolean, default=False)

    monitor = relationship("Monitor", back_populates="incidents")


class AlertLog(Base):
    __tablename__ = "alert_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    monitor_id = Column(String, ForeignKey("monitors.id"), nullable=False)
    monitor_name = Column(String, nullable=True)
    sent_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    channel = Column(String, nullable=False)   # "email", "sms", "telegram"
    alert_type = Column(String, nullable=False) # "down", "recovered", "slow"
    message = Column(Text, nullable=True)
    success = Column(Boolean, default=True)


class MaintenanceWindow(Base):
    __tablename__ = "maintenance_windows"

    id         = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    monitor_id = Column(String, ForeignKey("monitors.id", ondelete="CASCADE"), nullable=True)  # None = all monitors
    label      = Column(String, nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time   = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class JobApplication(Base):
    __tablename__ = "job_applications"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    company = Column(String, nullable=False)
    role = Column(String, nullable=False)
    status = Column(String, nullable=False, default="applied")
    job_url = Column(Text, nullable=True)
    ats_url = Column(Text, nullable=True)
    ats_detected = Column(String, nullable=True)
    ats_score = Column(Integer, nullable=True)
    source = Column(String, nullable=True)
    location = Column(String, nullable=True)
    resume_version = Column(String, nullable=True)
    job_description = Column(Text, nullable=True)
    strength_score = Column(Integer, nullable=True)
    missing_keywords = Column(Text, nullable=True)
    contact_name = Column(String, nullable=True)
    contact_email = Column(String, nullable=True)
    email_tracking_status = Column(String, nullable=True, default="not_sent")
    tracking_pixel_id = Column(String, nullable=True)
    email_sent_at = Column(DateTime(timezone=True), nullable=True)
    email_opened_at = Column(DateTime(timezone=True), nullable=True)
    email_open_count = Column(Integer, default=0)
    resume_download_id = Column(String, nullable=True)
    resume_filename = Column(String, nullable=True)
    resume_downloaded_at = Column(DateTime(timezone=True), nullable=True)
    resume_download_count = Column(Integer, default=0)
    linkedin_profile_viewed = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)
    applied_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    follow_up_at = Column(DateTime(timezone=True), nullable=True)
    interview_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class VisitorSession(Base):
    __tablename__ = "visitor_sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    site_url = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)
    location = Column(String, nullable=True)
    user_agent = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    last_activity_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    is_active = Column(Boolean, default=True)

    events = relationship("VisitorEvent", back_populates="session", cascade="all, delete")


class VisitorEvent(Base):
    __tablename__ = "visitor_events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("visitor_sessions.id", ondelete="CASCADE"), nullable=False)
    event_type = Column(String, nullable=False)
    target_element = Column(String, nullable=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    session = relationship("VisitorSession", back_populates="events")


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        for sql in [
            "ALTER TABLE job_applications ADD COLUMN IF NOT EXISTS ats_detected VARCHAR",
            "ALTER TABLE job_applications ADD COLUMN IF NOT EXISTS ats_score INTEGER",
            "ALTER TABLE job_applications ADD COLUMN IF NOT EXISTS job_description TEXT",
            "ALTER TABLE job_applications ADD COLUMN IF NOT EXISTS strength_score INTEGER",
            "ALTER TABLE job_applications ADD COLUMN IF NOT EXISTS missing_keywords TEXT",
            "ALTER TABLE job_applications ADD COLUMN IF NOT EXISTS email_tracking_status VARCHAR DEFAULT 'not_sent'",
            "ALTER TABLE job_applications ADD COLUMN IF NOT EXISTS tracking_pixel_id VARCHAR",
            "ALTER TABLE job_applications ADD COLUMN IF NOT EXISTS email_sent_at TIMESTAMPTZ",
            "ALTER TABLE job_applications ADD COLUMN IF NOT EXISTS email_opened_at TIMESTAMPTZ",
            "ALTER TABLE job_applications ADD COLUMN IF NOT EXISTS email_open_count INTEGER DEFAULT 0",
            "ALTER TABLE job_applications ADD COLUMN IF NOT EXISTS resume_download_id VARCHAR",
            "ALTER TABLE job_applications ADD COLUMN IF NOT EXISTS resume_filename VARCHAR",
            "ALTER TABLE job_applications ADD COLUMN IF NOT EXISTS resume_downloaded_at TIMESTAMPTZ",
            "ALTER TABLE job_applications ADD COLUMN IF NOT EXISTS resume_download_count INTEGER DEFAULT 0",
            "ALTER TABLE job_applications ADD COLUMN IF NOT EXISTS linkedin_profile_viewed BOOLEAN DEFAULT FALSE",
        ]:
            try:
                await conn.execute(text(sql))
            except Exception:
                pass
