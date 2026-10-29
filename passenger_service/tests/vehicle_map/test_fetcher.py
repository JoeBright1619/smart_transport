from __future__ import annotations

import pytest
from aioresponses import aioresponses

from passenger_service.vehicle_map.fetcher import VehicleMapFetcher

BACKEND = "http://backend.test"
TOKEN = "stk-test-token"


def _vehicle(
    vehicle_id: str,
    tenant_id: str = "ten-1",
    route_id: str | None = "rt-1",
    seating_capacity: int = 45,
    current_occupancy: int | None = 0,
    include_occupancy: bool = True,
) -> dict:
    """Build a wire-shaped VehicleRead row (camelCase)."""
    row = {
        "id": vehicle_id,
        "tenantId": tenant_id,
        "registrationNumber": "RAD 001 A",
        "model": "Yutong ZK6120",
        "seatingCapacity": seating_capacity,
        "status": "active",
        "speed": 35,
        "heading": 90,
        "fuel": 75,
        "engineStatus": "good",
        "routeId": route_id,
        "driverId": None,
        "plannedLoops": 5,
        "completedLoops": 2,
        "lastUpdate": "2026-04-08T17:00:00Z",
        "currentLocation": {"lat": -1.29, "lng": 36.82},
        "remainingSeats": max(0, seating_capacity - (current_occupancy or 0)),
    }
    if include_occupancy:
        row["currentOccupancy"] = current_occupancy
    return row


def _page(rows: list[dict], total: int, page: int = 1, page_size: int = 100) -> dict:
    return {
        "data": rows,
        "meta": {"total": total, "page": page, "pageSize": page_size},
    }


def _mock_url(page: int = 1) -> str:
    return f"{BACKEND}/api/v1/vehicles" f"?status=active&page={page}&page_size=100"


async def test_maps_camelcase_wire_to_snake_fields() -> None:
    fetcher = VehicleMapFetcher(BACKEND, TOKEN)
    try:
        with aioresponses() as m:
            m.get(
                _mock_url(),
                payload=_page(
                    [
                        _vehicle(
                            "veh-1",
                            tenant_id="ten-a",
                            route_id="rt-9",
                            seating_capacity=60,
                            current_occupancy=12,
                        )
                    ],
                    total=1,
                ),
            )
            vehicles = await fetcher.fetch_active_vehicles()
    finally:
        await fetcher.close()

    assert len(vehicles) == 1
    v = vehicles[0]
    assert v.vehicle_id == "veh-1"
    assert v.tenant_id == "ten-a"
    assert v.route_id == "rt-9"
    assert v.seating_capacity == 60
    assert v.current_occupancy == 12


async def test_skips_vehicles_with_no_route_id() -> None:
    fetcher = VehicleMapFetcher(BACKEND, TOKEN)
    try:
        with aioresponses() as m:
            m.get(
                _mock_url(),
                payload=_page(
                    [
                        _vehicle("veh-a", route_id="rt-1"),
                        _vehicle("veh-b", route_id=None),
                        _vehicle("veh-c", route_id="rt-2"),
                    ],
                    total=3,
                ),
            )
            vehicles = await fetcher.fetch_active_vehicles()
    finally:
        await fetcher.close()

    assert [v.vehicle_id for v in vehicles] == ["veh-a", "veh-c"]


async def test_reads_non_zero_occupancy() -> None:
    fetcher = VehicleMapFetcher(BACKEND, TOKEN)
    try:
        with aioresponses() as m:
            m.get(
                _mock_url(),
                payload=_page(
                    [_vehicle("veh-1", seating_capacity=45, current_occupancy=30)],
                    total=1,
                ),
            )
            vehicles = await fetcher.fetch_active_vehicles()
    finally:
        await fetcher.close()

    assert vehicles[0].current_occupancy == 30


async def test_missing_occupancy_defaults_to_zero() -> None:
    fetcher = VehicleMapFetcher(BACKEND, TOKEN)
    try:
        with aioresponses() as m:
            m.get(
                _mock_url(),
                payload=_page([_vehicle("veh-1", include_occupancy=False)], total=1),
            )
            vehicles = await fetcher.fetch_active_vehicles()
    finally:
        await fetcher.close()

    assert vehicles[0].current_occupancy == 0


async def test_null_occupancy_defaults_to_zero() -> None:
    fetcher = VehicleMapFetcher(BACKEND, TOKEN)
    try:
        with aioresponses() as m:
            m.get(
                _mock_url(),
                payload=_page([_vehicle("veh-1", current_occupancy=None)], total=1),
            )
            vehicles = await fetcher.fetch_active_vehicles()
    finally:
        await fetcher.close()

    assert vehicles[0].current_occupancy == 0


async def test_empty_page_returns_empty_list() -> None:
    fetcher = VehicleMapFetcher(BACKEND, TOKEN)
    try:
        with aioresponses() as m:
            m.get(_mock_url(), payload=_page([], total=0))
            vehicles = await fetcher.fetch_active_vehicles()
    finally:
        await fetcher.close()

    assert vehicles == []


async def test_paginates_until_total_reached() -> None:
    fetcher = VehicleMapFetcher(BACKEND, TOKEN)
    try:
        with aioresponses() as m:
            # Two pages: 100 + 1, total 101.
            page1 = [_vehicle(f"veh-{i:03d}", route_id="rt-1") for i in range(100)]
            page2 = [_vehicle("veh-100", route_id="rt-1")]
            m.get(_mock_url(page=1), payload=_page(page1, total=101, page=1))
            m.get(_mock_url(page=2), payload=_page(page2, total=101, page=2))

            vehicles = await fetcher.fetch_active_vehicles()
    finally:
        await fetcher.close()

    assert len(vehicles) == 101
    assert vehicles[-1].vehicle_id == "veh-100"


async def test_sends_service_token_and_status_filter() -> None:
    fetcher = VehicleMapFetcher(BACKEND, TOKEN)
    try:
        with aioresponses() as m:
            m.get(_mock_url(), payload=_page([], total=0))
            await fetcher.fetch_active_vehicles()

            # aioresponses stores calls in m.requests; assert header + params.
            key = ("GET", m.requests.keys().__iter__().__next__()[1])
            call = m.requests[key][0]
            assert call.kwargs["headers"] == {"X-Service-Token": TOKEN}
            assert call.kwargs["params"] == {
                "status": "active",
                "page": 1,
                "page_size": 100,
            }
    finally:
        await fetcher.close()


async def test_missing_tenant_id_raises() -> None:
    fetcher = VehicleMapFetcher(BACKEND, TOKEN)
    try:
        with aioresponses() as m:
            row = _vehicle("veh-1")
            del row["tenantId"]
            m.get(_mock_url(), payload=_page([row], total=1))

            with pytest.raises(KeyError):
                await fetcher.fetch_active_vehicles()
    finally:
        await fetcher.close()


async def test_empty_service_token_rejected() -> None:
    with pytest.raises(ValueError):
        VehicleMapFetcher(BACKEND, "")


async def test_pagination_terminates_when_rows_are_skipped() -> None:
    """A skipped row still counts toward Meta.total; the loop must not
    over-fetch past the last page. Regression for a bug where the
    loop used len(results) >= total."""
    fetcher = VehicleMapFetcher(BACKEND, TOKEN)
    try:
        with aioresponses() as m:
            # total=3 but only 2 rows kept (one has no route_id).
            m.get(
                _mock_url(page=1),
                payload=_page(
                    [
                        _vehicle("veh-a", route_id="rt-1"),
                        _vehicle("veh-b", route_id=None),
                        _vehicle("veh-c", route_id="rt-2"),
                    ],
                    total=3,
                    page=1,
                ),
            )
            # No page 2 mock: a second request would raise.
            vehicles = await fetcher.fetch_active_vehicles()
    finally:
        await fetcher.close()

    assert [v.vehicle_id for v in vehicles] == ["veh-a", "veh-c"]
