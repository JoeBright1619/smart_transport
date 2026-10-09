"""Issue a service token for a tenant.

Usage:
    python -m scripts.issue_service_token --tenant-id ten-... --name gps-sim-prod
    python -m scripts.issue_service_token --tenant-id ten-... --name gps-sim-dev --dev
"""

from __future__ import annotations

import argparse
import asyncio

from app.core.database import AsyncSessionLocal
from app.services.service_token_service import issue_token


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tenant-id", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--scopes", default="vehicles:read")
    parser.add_argument("--dev", action="store_true")
    args = parser.parse_args()

    async with AsyncSessionLocal() as db:
        row, plaintext = await issue_token(
            db,
            tenant_id=args.tenant_id,
            name=args.name,
            scopes=args.scopes,
            dev=args.dev,
        )
        await db.commit()

    print("Service token created. Store this value now — it will not be shown again.")
    print(f"  id     : {row.id}")
    print(f"  tenant : {row.tenant_id}")
    print(f"  name   : {row.name}")
    print(f"  scopes : {row.scopes}")
    print(f"  token  : {plaintext}")


if __name__ == "__main__":
    asyncio.run(main())
