"""Tests for superadmin passenger transport usage report endpoint."""

from __future__ import annotations


from tests.conftest import auth_headers


# ---------------------------------------------------------------------------
# GET /superadmin/passengers/{id}/report
# ---------------------------------------------------------------------------


async def test_passenger_report_zero_boardings_returns_non_error(
    client, superadmin, passenger_user
):
    """A passenger with no boarding records returns totalBoardings=0, not an error."""
    r = await client.get(
        f"/superadmin/passengers/{passenger_user.id}/report",
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
    assert data["passengerId"] == passenger_user.id
