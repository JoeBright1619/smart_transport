from gps_service.vehicle_tracker.wire import camel_to_snake, normalize_keys


def test_camel_to_snake_basic():
    assert camel_to_snake("currentLocation") == "current_location"
    assert camel_to_snake("routeId") == "route_id"
    assert camel_to_snake("lastUpdate") == "last_update"
    assert camel_to_snake("id") == "id"
    assert camel_to_snake("registrationNumber") == "registration_number"


def test_normalize_keys_nested():
    raw = {
        "routeId": "r1",
        "currentLocation": {"lat": -1.0, "lng": 30.0},
        "tags": [{"tagName": "a"}, {"tagName": "b"}],
    }
    assert normalize_keys(raw) == {
        "route_id": "r1",
        "current_location": {"lat": -1.0, "lng": 30.0},
        "tags": [{"tag_name": "a"}, {"tag_name": "b"}],
    }


def test_normalize_keys_preserves_scalars():
    assert normalize_keys(5) == 5
    assert normalize_keys("x") == "x"
    assert normalize_keys(None) is None
