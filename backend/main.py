from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.core.config import settings
from app.core.database import engine
from app.services.simulation_runner import (
    start_vehicle_simulation,
    stop_vehicle_simulation,
)
from app.routers import (
    alerts,
    analytics,
    arrivals,
    auth,
    drivers,
    maintenance,
    routes,
    stops,
    superadmin,
    trips,
    users,
    vehicles,
)
from app.websocket import tracking


def _error_response(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "data": None,
            "meta": None,
            "error": {
                "code": code,
                "message": message,
            },
        },
    )


def _is_error_envelope(detail: Any) -> bool:
    return (
        isinstance(detail, dict)
        and detail.get("data") is None
        and detail.get("meta") is None
        and isinstance(detail.get("error"), dict)
        and isinstance(detail["error"].get("code"), str)
        and isinstance(detail["error"].get("message"), str)
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))

    start_vehicle_simulation()

    try:
        yield
    finally:
        await stop_vehicle_simulation()

    await engine.dispose()


_TAGS_METADATA = [
    {
        "name": "auth",
        "description": "Registration, login, token refresh, and logout.",
    },
    {
        "name": "users",
        "description": "Manage users within a tenant. Admins can invite and remove members.",
    },
    {
        "name": "vehicles",
        "description": "Fleet vehicle registry — create, track status, and retire buses.",
    },
    {
        "name": "routes",
        "description": "Bus routes with ordered stops. Routes are shared across all authenticated roles.",
    },
    {
        "name": "drivers",
        "description": "Driver profiles, licence/certification tracking, and status management.",
    },
    {
        "name": "trips",
        "description": "Trip scheduling and lifecycle (scheduled → active → completed/cancelled).",
    },
    {
        "name": "alerts",
        "description": "System-generated alerts for vehicles and routes. Supports acknowledgement.",
    },
    {
        "name": "maintenance",
        "description": "Vehicle maintenance records — schedule, track, and complete service jobs.",
    },
    {
        "name": "analytics",
        "description": "Aggregated fleet KPIs and daily breakdown for a configurable date window.",
    },
    {
        "name": "arrivals",
        "description": "Real-time ETA estimates for active vehicles approaching a stop.",
    },
    {
        "name": "superadmin",
        "description": "Platform-level management: tenant suspension, impersonation, and global analytics.",
    },
]


def create_app() -> FastAPI:
    app = FastAPI(
        title="Smart Transport API",
        version="0.1.0",
        description=(
            "Multi-tenant public-transport management platform. "
            "Covers fleet, drivers, routes, trips, maintenance, real-time tracking, "
            "alerts, and analytics."
        ),
        openapi_tags=_TAGS_METADATA,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.CORS_ORIGINS),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth.router)
    app.include_router(users.router)
    app.include_router(vehicles.router)
    app.include_router(routes.router)
    app.include_router(stops.router)
    app.include_router(trips.router)
    app.include_router(drivers.router)
    app.include_router(maintenance.router)
    app.include_router(alerts.router)
    app.include_router(analytics.router)
    app.include_router(arrivals.router)
    app.include_router(superadmin.router, prefix="/superadmin")
    app.include_router(tracking.router)

    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        request: Request,
        exc: HTTPException,
    ) -> JSONResponse:
        if _is_error_envelope(exc.detail):
            return JSONResponse(status_code=exc.status_code, content=exc.detail)

        message = exc.detail if isinstance(exc.detail, str) else "HTTP error"
        return _error_response(exc.status_code, "HTTP_ERROR", message)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        return _error_response(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "VALIDATION_ERROR",
            "Request validation failed",
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        message = str(exc) if settings.DEBUG else "Internal server error"
        return _error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "INTERNAL_SERVER_ERROR",
            message,
        )

    return app


app = create_app()
