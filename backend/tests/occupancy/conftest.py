"""Occupancy-domain fixtures.

SQLite disables foreign-key enforcement per connection by default. The
occupancy tables rely on ``ON DELETE CASCADE`` (boarding_passenger_events ←
occupancy_events) and ``ON DELETE SET NULL``
(boarding_passenger_events.passenger_id ← users), so this module enables the
pragma for the occupancy domain's tests only.

Enabling it globally in ``tests/conftest.py::test_engine`` exposed ~15
pre-existing tests that insert orphan FK rows and silently passed under
SQLite's default. Those are tracked separately; until they are fixed, this
pragma stays scoped to the occupancy domain so the cascade / SET NULL tests
here are still meaningful without gating this task on unrelated fixtures.
"""

from __future__ import annotations

import pytest
from sqlalchemy import event


@pytest.fixture(autouse=True)
async def _enable_sqlite_foreign_keys(test_engine):
    def _set_pragma(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    event.listen(test_engine.sync_engine, "connect", _set_pragma)
    try:
        yield
    finally:
        event.remove(test_engine.sync_engine, "connect", _set_pragma)
