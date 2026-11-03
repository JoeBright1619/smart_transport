from pathlib import Path
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    DEBUG: bool = False

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    CORS_ORIGINS: str | List[str]

    # Capacity alert (Task 7.2)
    CAPACITY_ALERT_THRESHOLD: float = 0.9
    CAPACITY_ALERT_DEDUP_SECONDS: int = 300

    DATABASE_URL: str
    REDIS_URL: str

    # MQTT
    MQTT_BROKER_URL: str = "localhost"
    MQTT_BROKER_PORT: int = 1883
    MQTT_USERNAME: str = ""
    MQTT_PASSWORD: str = ""
    MQTT_CLIENT_ID: str = "smart-transport-backend"

    # Dev-only bootstrap service token. Prefer real rows in `service_tokens`.
    # If set, this token is accepted and maps to GPS_SERVICE_TENANT_ID.
    GPS_SERVICE_TOKEN: str = ""
    GPS_SERVICE_TENANT_ID: str = ""

    # Email (Gmail SMTP — use an App Password, not your account password)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_NAME: str = "Smart Transport"

    # Frontend base URL (used to build invitation links)
    FRONTEND_URL: str = "http://localhost:5173"

    # "smtp" sends via Gmail SMTP; "console" prints to the logger (dev/test)
    EMAIL_BACKEND: str = "console"

    model_config = SettingsConfigDict(
        env_file=_BACKEND_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | List[str]) -> str | List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        return v


settings = Settings()
