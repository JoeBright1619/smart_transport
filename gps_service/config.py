from pydantic_settings import BaseSettings, SettingsConfigDict


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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = GPSServiceSettings()
