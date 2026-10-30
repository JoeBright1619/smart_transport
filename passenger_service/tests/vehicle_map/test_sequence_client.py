from __future__ import annotations

import aiohttp
import pytest
from aioresponses import aioresponses

from passenger_service.vehicle_map.sequence_client import SequenceClient

BACKEND = "http://backend.test"
TOKEN = "stk-universal"
VEHICLE_ID = "veh-abc"


def _seq_url() -> str:
    return f"{BACKEND}/api/v1/service/vehicles/" f"{VEHICLE_ID}/latest-arrival-sequence"


def _ok(value: int) -> dict:
    return {
        "data": {"arrivalSequence": value},
        "meta": None,
        "error": None,
    }


def _err(code: str) -> dict:
    return {
        "data": None,
        "meta": None,
        "error": {"code": code, "message": code},
    }


async def test_returns_sequence_on_200() -> None:
    client = SequenceClient(BACKEND, TOKEN)
    try:
        with aioresponses() as m:
            m.get(_seq_url(), payload=_ok(7))
            seq = await client.fetch_latest_sequence(VEHICLE_ID)
    finally:
        await client.close()
    assert seq == 7


async def test_returns_zero_on_vehicle_not_found() -> None:
    client = SequenceClient(BACKEND, TOKEN)
    try:
        with aioresponses() as m:
            m.get(_seq_url(), status=404, payload=_err("vehicle_not_found"))
            seq = await client.fetch_latest_sequence(VEHICLE_ID)
    finally:
        await client.close()
    assert seq == 0


async def test_returns_zero_on_no_arrival_records() -> None:
    client = SequenceClient(BACKEND, TOKEN)
    try:
        with aioresponses() as m:
            m.get(_seq_url(), status=404, payload=_err("no_arrival_records"))
            seq = await client.fetch_latest_sequence(VEHICLE_ID)
    finally:
        await client.close()
    assert seq == 0


async def test_unknown_404_code_raises() -> None:
    client = SequenceClient(BACKEND, TOKEN)
    try:
        with aioresponses() as m:
            m.get(_seq_url(), status=404, payload=_err("route_not_found"))
            with pytest.raises(aiohttp.ClientResponseError):
                await client.fetch_latest_sequence(VEHICLE_ID)
    finally:
        await client.close()


async def test_non_json_404_raises() -> None:
    """A 404 with a non-JSON body (misrouted proxy) must raise, not
    silently return 0."""

    client = SequenceClient(BACKEND, TOKEN)
    try:
        with aioresponses() as m:
            m.get(_seq_url(), status=404, body="<html>Not Found</html>")
            with pytest.raises(aiohttp.ClientResponseError):
                await client.fetch_latest_sequence(VEHICLE_ID)
    finally:
        await client.close()


async def test_500_raises() -> None:
    client = SequenceClient(BACKEND, TOKEN)
    try:
        with aioresponses() as m:
            m.get(_seq_url(), status=500, body="boom")
            with pytest.raises(aiohttp.ClientResponseError):
                await client.fetch_latest_sequence(VEHICLE_ID)
    finally:
        await client.close()


async def test_timeout_raises() -> None:
    client = SequenceClient(BACKEND, TOKEN)
    try:
        with aioresponses() as m:
            m.get(_seq_url(), exception=aiohttp.ServerTimeoutError("timeout"))
            with pytest.raises(aiohttp.ServerTimeoutError):
                await client.fetch_latest_sequence(VEHICLE_ID)
    finally:
        await client.close()


async def test_200_without_arrival_sequence_raises() -> None:
    client = SequenceClient(BACKEND, TOKEN)
    try:
        with aioresponses() as m:
            m.get(_seq_url(), payload={"data": {}, "meta": None, "error": None})
            with pytest.raises(ValueError):
                await client.fetch_latest_sequence(VEHICLE_ID)
    finally:
        await client.close()


async def test_empty_service_token_rejected() -> None:
    with pytest.raises(ValueError):
        SequenceClient(BACKEND, "")


async def test_sends_service_token_header() -> None:
    client = SequenceClient(BACKEND, TOKEN)
    try:
        with aioresponses() as m:
            m.get(_seq_url(), payload=_ok(1))
            await client.fetch_latest_sequence(VEHICLE_ID)

            calls = list(m.requests.values())
            assert calls
            headers = calls[0][0].kwargs.get("headers") or {}
            assert headers.get("X-Service-Token") == TOKEN
    finally:
        await client.close()
