"""Simple async retry helper.

Mirrors gps_service's _retry in api/app.py — copied, not imported
(architectural boundary, project context §1). Fixed-delay, not
exponential: `attempts` total calls spaced `delay` seconds apart. On
final failure, re-raises the last exception unchanged so callers can
handle or log it.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Awaitable, Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


async def retry(
    call: Callable[[], Awaitable[T]],
    *,
    attempts: int = 10,
    delay: float = 2.0,
    what: str = "operation",
) -> T:
    """Retry `call` up to `attempts` times, spaced `delay` seconds apart.

    Returns the result of the first successful call. On exhaustion,
    re-raises the last exception. The final attempt's sleep is skipped
    only in the sense that after the last attempt fails we raise — no
    wasted delay before giving up.
    """

    last_exc: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            return await call()
        except Exception as exc:
            last_exc = exc
            logger.warning("%s attempt %d/%d failed: %s", what, attempt, attempts, exc)
            if attempt < attempts:
                await asyncio.sleep(delay)

    if last_exc is None:
        # Unreachable: `attempts >= 1` guarantees at least one iteration.
        raise RuntimeError("retry loop ended without recording an exception")
    raise last_exc
