"""Entry point for passenger_service.

Thin uvicorn runner, mirroring gps_service/main.py. Uses the
module-level ``app`` created in passenger_service/api/app.py; the
lifespan wiring is identical to running via
``uvicorn passenger_service.api.app:app``.

For local dev with auto-reload, prefer the uvicorn CLI:

    uvicorn passenger_service.api.app:app --port 8002 --reload

Passing the app instance to uvicorn.run() disables --reload, so this
file is best used for production / container entry.
"""

from __future__ import annotations

import uvicorn

from passenger_service.api.app import create_app
from passenger_service.config import settings


def main() -> None:
    uvicorn.run(
        create_app(),
        host=settings.API_HOST,
        port=settings.API_PORT,
        log_level="info",
    )


if __name__ == "__main__":
    main()
