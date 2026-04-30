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
from app.routers import (
    alerts,
    analytics,
    auth,
    drivers,
    maintenance,
    routes,
    superadmin,
    trips,
    users,
    vehicles,
)


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

    yield

    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Smart Transport API",
        version="0.1.0",
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
    app.include_router(users.router, prefix="/api/v1")
    app.include_router(vehicles.router, prefix="/api/v1")
    app.include_router(routes.router, prefix="/api/v1")
    app.include_router(trips.router, prefix="/api/v1")
    app.include_router(drivers.router, prefix="/api/v1")
    app.include_router(maintenance.router, prefix="/api/v1")
    app.include_router(alerts.router, prefix="/api/v1")
    app.include_router(analytics.router, prefix="/api/v1")
    app.include_router(superadmin.router, prefix="/superadmin")

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
