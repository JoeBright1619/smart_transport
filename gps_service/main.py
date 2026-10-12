from __future__ import annotations

import uvicorn

from gps_service.api.app import create_app
from gps_service.config import settings


def main() -> None:
    uvicorn.run(
        create_app(),
        host=settings.API_HOST,
        port=settings.API_PORT,
        log_level="info",
    )


if __name__ == "__main__":
    main()
