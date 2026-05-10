"""
Run this once to add the new columns to your existing database.
Usage: docker compose exec api python migrate.py
"""
import asyncio
from sqlalchemy import text
from app.models.database import engine


async def migrate():
    async with engine.begin() as conn:
        # Add new columns to monitors table (ignore if already exists)
        migrations = [
            "ALTER TABLE monitors ADD COLUMN IF NOT EXISTS last_status VARCHAR",
            "ALTER TABLE monitors ADD COLUMN IF NOT EXISTS last_response_ms FLOAT",
            "ALTER TABLE monitors ADD COLUMN IF NOT EXISTS last_checked_at TIMESTAMPTZ",
            "ALTER TABLE monitors ADD COLUMN IF NOT EXISTS ssl_days_remaining INTEGER",
            "ALTER TABLE job_applications ADD COLUMN IF NOT EXISTS ats_detected VARCHAR",
            "ALTER TABLE job_applications ADD COLUMN IF NOT EXISTS ats_score INTEGER",
            "ALTER TABLE job_applications ADD COLUMN IF NOT EXISTS job_description TEXT",
            "ALTER TABLE job_applications ADD COLUMN IF NOT EXISTS strength_score INTEGER",
            "ALTER TABLE job_applications ADD COLUMN IF NOT EXISTS missing_keywords TEXT",
            "ALTER TABLE job_applications ADD COLUMN IF NOT EXISTS email_tracking_status VARCHAR DEFAULT 'not_sent'",
            "ALTER TABLE job_applications ADD COLUMN IF NOT EXISTS tracking_pixel_id VARCHAR",
            "ALTER TABLE job_applications ADD COLUMN IF NOT EXISTS email_sent_at TIMESTAMPTZ",
            "ALTER TABLE job_applications ADD COLUMN IF NOT EXISTS email_opened_at TIMESTAMPTZ",
            "ALTER TABLE job_applications ADD COLUMN IF NOT EXISTS linkedin_profile_viewed BOOLEAN DEFAULT FALSE",
            # Rename response_time_ms → response_ms in check_results
            "ALTER TABLE check_results RENAME COLUMN response_time_ms TO response_ms",
        ]
        for sql in migrations:
            try:
                await conn.execute(text(sql))
                print(f"✓ {sql}")
            except Exception as e:
                print(f"⚠ Skipped: {sql}\n  Reason: {e}")

    print("\n✅ Migration complete!")


if __name__ == "__main__":
    asyncio.run(migrate())
