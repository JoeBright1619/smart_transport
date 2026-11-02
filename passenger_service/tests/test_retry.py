"""Tests for the async retry helper."""

from __future__ import annotations

import pytest

from passenger_service.retry import retry


async def test_retry_returns_on_first_success() -> None:
    """No failure → single call, returns immediately."""

    calls = [0]

    async def ok():
        calls[0] += 1
        return "value"

    result = await retry(ok, attempts=3, delay=0.0)
    assert result == "value"
    assert calls[0] == 1


async def test_retry_succeeds_after_transient_failures() -> None:
    """Some attempts fail, then one succeeds — returns the successful value."""
    calls = [0]

    async def flaky():
        calls[0] += 1
        if calls[0] < 3:
            raise RuntimeError(f"fail {calls[0]}")
        return "ok"

    result = await retry(flaky, attempts=5, delay=0.0)
    assert result == "ok"
    # Succeeded on attempt 3; should not have made attempts 4 or 5.
    assert calls[0] == 3


async def test_retry_exhausts_and_raises_last_exception() -> None:
    """All attempts fail — raises the last exception, having tried every attempt."""

    calls = [0]

    async def bad():
        calls[0] += 1
        raise RuntimeError(f"fail {calls[0]}")

    with pytest.raises(RuntimeError, match="fail 3"):
        await retry(bad, attempts=3, delay=0.0)
    assert calls[0] == 3


async def test_retry_zero_attempts_raises_runtime_error() -> None:
    """attempts=0 is a caller bug: no call is made, and we raise instead of
    silently returning None or hanging."""

    calls = [0]

    async def ok():
        calls[0] += 1
        return "value"

    with pytest.raises(RuntimeError):
        await retry(ok, attempts=0)
    assert calls[0] == 0
