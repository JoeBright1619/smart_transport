from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_PATH = Path(__file__).resolve().parent / ".env"


class GPSServiceSettings(BaseSettings):
    MQTT_BROKER_URL: str = "localhost"
    MQTT_BROKER_PORT: int = 1883
    MQTT_USERNAME: str = ""
    MQTT_PASSWORD: str = ""
    MQTT_CLIENT_ID: str = "smart-transport-gps-service"

    POLL_INTERVAL: float = 5.0
    SIMULATION_MODE: bool = True

    MQTT_RETRY_ATTEMPTS: int = 3
    MQTT_RETRY_DELAY: float = 2.0

    # Backend API
    BACKEND_BASE_URL: str = "http://localhost:8000"

    BACKEND_SERVICE_TOKEN: str = ""
    BACKEND_REQUEST_TIMEOUT: float = 10.0
    BACKEND_PAGE_SIZE: int = 100

    # Synthetic device id assigned to each tracked vehicle
    DEVICE_ID_PREFIX: str = "sim"

    VEHICLE_REFRESH_INTERVAL: float = 30.0

    model_config = SettingsConfigDict(
        env_file=_ENV_PATH,
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = GPSServiceSettings()
