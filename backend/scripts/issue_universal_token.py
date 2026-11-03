"""Issue a universal service token for passenger_service.

Usage (from backend/, venv active):
    python scripts/issue_universal_token.py

Prints the plaintext token once. Copy it into
passenger_service/.env as PASSENGER_POOL_SERVICE_TOKEN.

Requires the DB to be reachable (same env as the running backend).
"""

from __future__ import annotations

import asyncio
import sys

from app.core.database import AsyncSessionLocal
from app.services.service_token_service import issue_token


SCOPES = "passengers:read_universal,vehicles:read_universal"
NAME = "passenger-service"


async def main() -> int:
    async with AsyncSessionLocal() as db:
        row, plaintext = await issue_token(
            db,
            universal=True,
            name=NAME,
            scopes=SCOPES,
        )
        await db.commit()

        print("Issued universal service token")
        print(f"  id:        {row.id}")
        print(f"  name:      {row.name}")
        print(f"  universal: {row.tenant_id is None}")
        print(f"  scopes:    {row.scopes}")
        print()
        print("Plaintext (shown once, store in passenger_service/.env):")
        print(f"  PASSENGER_POOL_SERVICE_TOKEN={plaintext}")
        return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
