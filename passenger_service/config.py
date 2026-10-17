from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_PATH = Path(__file__).resolve().parent / ".env"


class PassengerServiceSettings(BaseSettings):
    API_HOST: str = "0.0.0.0"  # nosec B104
    API_PORT: int = 8002
    MQTT_BROKER_URL: str = "localhost"
    MQTT_BROKER_PORT: int = 1883
    MQTT_USERNAME: str = ""
    MQTT_PASSWORD: str = ""
    MQTT_CLIENT_ID: str = "smart-transport-passenger-service"

    MQTT_RETRY_ATTEMPTS: int = 3
    MQTT_RETRY_DELAY: float = 2.0

    # Backend API
    BACKEND_BASE_URL: str = "http://localhost:8000"
    BACKEND_SERVICE_TOKEN: str = ""
    BACKEND_REQUEST_TIMEOUT: float = 10.0
    BACKEND_PAGE_SIZE: int = 100

    VEHICLE_REFRESH_INTERVAL: float = 30.0

    # Stop-arrival detection (design doc §3)
    STOP_ARRIVAL_RADIUS_M: float = 30.0
    STOP_SPEED_THRESHOLD_KMH: float = 5.0
    STOP_COOLDOWN_SECONDS: float = 60.0

    # Passenger simulation (design doc §7)
    CRUSH_CAPACITY_FACTOR: float = 1.15

    model_config = SettingsConfigDict(
        env_file=_ENV_PATH,
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = PassengerServiceSettings()
