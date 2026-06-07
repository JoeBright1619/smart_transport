"""Tests for superadmin passenger transport usage report endpoint."""

from __future__ import annotations

import pytest

from tests.conftest import auth_headers


@pytest.fixture
async def superadmin(make_user):
    return await make_user(tenant_id=None, role="superadmin")


@pytest.fixture
async def passenger(make_user):
    return await make_user(tenant_id=None, role="passenger")


# ---------------------------------------------------------------------------
# GET /superadmin/passengers/{id}/report
# ---------------------------------------------------------------------------


async def test_passenger_report_zero_boardings_returns_non_error(
    client, superadmin, passenger
):
    """A passenger with no boarding records returns totalBoardings=0, not an error."""
    r = await client.get(
        f"/superadmin/passengers/{passenger.id}/report",
        params={"date_from": "2024-01-01", "date_to": "2024-12-31"},
        headers=auth_headers(superadmin),
    )
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["totalBoardings"] == 0
    assert data["timeline"] == []
    assert data["mostUsedRoutes"] == []
    assert data["mostUsedStops"] == []
    assert "message" in data and data["message"] is not None
    assert data["passengerId"] == passenger.id
