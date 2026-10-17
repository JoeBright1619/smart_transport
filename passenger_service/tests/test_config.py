"""Tests for PassengerServiceSettings loading and field defaults."""

import importlib


from passenger_service.config import PassengerServiceSettings


def _reload_config(monkeypatch, env: dict[str, str]):
    """Reload the config module with a given env applied.

    ``settings`` is constructed at import time, so we must reload the module
    after mutating the environment for env-driven defaults to take effect.
    Clears the module from sys.modules first so the module-level ``settings``
    is rebuilt from the mutated environment.
    """
    import sys

    for key, value in env.items():
        monkeypatch.setenv(key, value)
    sys.modules.pop("passenger_service.config", None)
    return importlib.import_module("passenger_service.config")


def test_defaults_load():
    """Settings construct with expected defaults when no env is set."""
    s = PassengerServiceSettings()

    # API
    assert s.API_HOST == "0.0.0.0"
    assert s.API_PORT == 8002

    # MQTT
    assert s.MQTT_BROKER_URL == "localhost"
    assert s.MQTT_BROKER_PORT == 1883
    assert s.MQTT_USERNAME == ""
    assert s.MQTT_PASSWORD == ""
    assert s.MQTT_CLIENT_ID == "smart-transport-passenger-service"
    assert s.MQTT_RETRY_ATTEMPTS == 3
    assert s.MQTT_RETRY_DELAY == 2.0

    # Backend
    assert s.BACKEND_BASE_URL == "http://localhost:8000"
    assert s.BACKEND_SERVICE_TOKEN == ""
    assert s.BACKEND_REQUEST_TIMEOUT == 10.0
    assert s.BACKEND_PAGE_SIZE == 100
    assert s.VEHICLE_REFRESH_INTERVAL == 30.0

    # Detection (design doc §3)
    assert s.STOP_ARRIVAL_RADIUS_M == 30.0
    assert s.STOP_SPEED_THRESHOLD_KMH == 5.0
    assert s.STOP_COOLDOWN_SECONDS == 60.0

    # Simulation (design doc §7)
    assert s.CRUSH_CAPACITY_FACTOR == 1.15


def test_fields_required_by_task_0_1_are_present():
    """Every field the implementation plan's Task 0.1 enumerates exists."""
    required = {
        "MQTT_BROKER_URL",
        "MQTT_BROKER_PORT",
        "MQTT_USERNAME",
        "MQTT_PASSWORD",
        "MQTT_CLIENT_ID",
        "MQTT_RETRY_ATTEMPTS",
        "MQTT_RETRY_DELAY",
        "BACKEND_BASE_URL",
        "BACKEND_SERVICE_TOKEN",
        "BACKEND_REQUEST_TIMEOUT",
        "BACKEND_PAGE_SIZE",
        "VEHICLE_REFRESH_INTERVAL",
        "API_HOST",
        "API_PORT",
        "STOP_ARRIVAL_RADIUS_M",
        "STOP_SPEED_THRESHOLD_KMH",
        "STOP_COOLDOWN_SECONDS",
        "CRUSH_CAPACITY_FACTOR",
    }
    model_fields = set(PassengerServiceSettings.model_fields.keys())
    missing = required - model_fields
    assert not missing, f"Missing fields: {sorted(missing)}"


def test_overrides_from_env(monkeypatch):
    """Env vars override defaults (case-sensitive, matching gps_service)."""
    mod = _reload_config(
        monkeypatch,
        {
            "API_PORT": "9999",
            "MQTT_BROKER_URL": "broker.example",
            "BACKEND_SERVICE_TOKEN": "tok-abc",
            "STOP_ARRIVAL_RADIUS_M": "15.5",
            "CRUSH_CAPACITY_FACTOR": "1.25",
        },
    )
    s = mod.settings

    assert s.API_PORT == 9999
    assert s.MQTT_BROKER_URL == "broker.example"
    assert s.BACKEND_SERVICE_TOKEN == "tok-abc"
    assert s.STOP_ARRIVAL_RADIUS_M == 15.5
    assert s.CRUSH_CAPACITY_FACTOR == 1.25

    # Untouched fields keep their defaults.
    assert s.API_HOST == "0.0.0.0"
    assert s.STOP_COOLDOWN_SECONDS == 60.0
