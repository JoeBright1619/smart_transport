from __future__ import annotations

import pytest
from aioresponses import aioresponses

from passenger_service.passenger_pool.fetcher import PassengerPoolFetcher

BACKEND = "http://backend.test"
TOKEN = "stk-universal-token"


def _pax(passenger_id: str) -> dict:
    """Minimal wire row — only id matters to the fetcher."""
    return {"id": passenger_id}


def _page(rows: list[dict], total: int, page: int = 1, page_size: int = 100) -> dict:
    return {
        "data": rows,
        "meta": {"total": total, "page": page, "pageSize": page_size},
    }


def _mock_url(page: int = 1) -> str:
    return f"{BACKEND}/api/v1/passengers?page={page}&page_size=100"


async def test_fetches_all_ids_single_page() -> None:
    fetcher = PassengerPoolFetcher(BACKEND, TOKEN)
    try:
        with aioresponses() as m:
            m.get(_mock_url(), payload=_page([_pax("pas-1"), _pax("pas-2")], total=2))
            ids = await fetcher.fetch_passenger_ids()
    finally:
        await fetcher.close()

    assert ids == ["pas-1", "pas-2"]


async def test_paginates_until_total_reached() -> None:
    fetcher = PassengerPoolFetcher(BACKEND, TOKEN)
    try:
        with aioresponses() as m:
            page1 = [_pax(f"pas-{i:03d}") for i in range(100)]
            page2 = [_pax("pas-100")]
            m.get(_mock_url(page=1), payload=_page(page1, total=101, page=1))
            m.get(_mock_url(page=2), payload=_page(page2, total=101, page=2))
            ids = await fetcher.fetch_passenger_ids()
    finally:
        await fetcher.close()

    assert len(ids) == 101
    assert ids[-1] == "pas-100"


async def test_empty_pool_returns_empty_list() -> None:
    fetcher = PassengerPoolFetcher(BACKEND, TOKEN)
    try:
        with aioresponses() as m:
            m.get(_mock_url(), payload=_page([], total=0))
            ids = await fetcher.fetch_passenger_ids()
            cached = fetcher.cached_ids()
    finally:
        await fetcher.close()

    assert ids == []
    assert list(cached) == []


async def test_request_has_no_tenant_id_param() -> None:
    """Passengers are universal — the request must not carry tenant_id."""

    fetcher = PassengerPoolFetcher(BACKEND, TOKEN)
    try:
        with aioresponses() as m:
            m.get(_mock_url(), payload=_page([], total=0))
            await fetcher.fetch_passenger_ids()

            calls = list(m.requests.values())
            assert calls, "expected a mocked call"
            params = calls[0][0].kwargs.get("params") or {}
            assert "tenant_id" not in params
            assert "tenantId" not in params
    finally:
        await fetcher.close()


async def test_sends_service_token_header() -> None:
    fetcher = PassengerPoolFetcher(BACKEND, TOKEN)
    try:
        with aioresponses() as m:
            m.get(_mock_url(), payload=_page([], total=0))
            await fetcher.fetch_passenger_ids()

            calls = list(m.requests.values())
            assert calls, "expected a mocked call"
            headers = calls[0][0].kwargs.get("headers") or {}
            assert headers.get("X-Service-Token") == TOKEN
    finally:
        await fetcher.close()


async def test_cached_ids_before_first_fetch_is_empty() -> None:
    fetcher = PassengerPoolFetcher(BACKEND, TOKEN)
    try:
        assert list(fetcher.cached_ids()) == []
    finally:
        await fetcher.close()


async def test_cached_ids_does_not_trigger_http() -> None:
    """cached_ids() is a pure reader — only fetch_passenger_ids() hits the network."""

    fetcher = PassengerPoolFetcher(BACKEND, TOKEN)
    try:
        with aioresponses() as m:
            m.get(_mock_url(), payload=_page([_pax("pas-1")], total=1))
            await fetcher.fetch_passenger_ids()

            # No new mock registered; a second HTTP call would raise.
            first = fetcher.cached_ids()
            second = fetcher.cached_ids()

            assert list(first) == ["pas-1"]
            assert first == second
    finally:
        await fetcher.close()


async def test_refresh_after_interval(monkeypatch: pytest.MonkeyPatch) -> None:
    """After the refresh interval, calling fetch_passenger_ids() again
    performs a new HTTP request. is_stale() reflects the TTL."""

    fetcher = PassengerPoolFetcher(BACKEND, TOKEN, refresh_interval=30.0)

    now = [1000.0]
    monkeypatch.setattr(
        "passenger_service.passenger_pool.fetcher.time.monotonic",
        lambda: now[0],
    )

    try:
        with aioresponses() as m:
            m.get(_mock_url(), payload=_page([_pax("pas-1")], total=1))
            m.get(_mock_url(), payload=_page([_pax("pas-2")], total=1))

            await fetcher.fetch_passenger_ids()
            assert list(fetcher.cached_ids()) == ["pas-1"]
            assert fetcher.is_stale() is False

            now[0] += 31.0
            assert fetcher.is_stale() is True
            await fetcher.fetch_passenger_ids()
            assert list(fetcher.cached_ids()) == ["pas-2"]
    finally:
        await fetcher.close()


async def test_empty_service_token_rejected() -> None:
    with pytest.raises(ValueError):
        PassengerPoolFetcher(BACKEND, "")
