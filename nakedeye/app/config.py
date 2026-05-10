from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "postgresql+asyncpg://nakedeye:secret@db:5432/nakedeye"
    SECRET_KEY: str = "change-me"
    API_KEY: str = ""
    ALLOWED_ORIGINS: str = "http://localhost:8000,http://127.0.0.1:8000"
    ALLOWED_HOSTS: str = "*"
    TRUSTED_CLIENTS: str = "127.0.0.1,::1,localhost,172.17.0.1,172.18.0.1"
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = ""
    SESSION_COOKIE_SECURE: bool = False
    LOGIN_MAX_ATTEMPTS: int = 5
    LOGIN_LOCKOUT_SECONDS: int = 300
    MAX_REQUEST_BYTES: int = 1048576

    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASS: str = ""
    ALERT_EMAIL_TO: str = ""

    SEMAPHORE_API_KEY: str = ""
    ALERT_SMS_TO: str = ""

    # Social Media
    YOUTUBE_API_KEY: str = ""
    YOUTUBE_CHANNEL_ID: str = ""
    FACEBOOK_PAGE_ID: str = ""
    FACEBOOK_ACCESS_TOKEN: str = ""
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""

settings = Settings()


def reload_settings() -> Settings:
    new_settings = Settings()
    for field_name in Settings.model_fields:
        setattr(settings, field_name, getattr(new_settings, field_name))
    return settings
