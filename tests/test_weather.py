import pytest

from pyutils.weather import (
    FORECAST_URL,
    GEOCODE_URL,
    Place,
    c_to_f,
    forecast,
    format_report,
    geocode,
)

GEO: dict[str, object] = {
    "results": [
        {
            "name": "Chicago",
            "country": "United States",
            "latitude": 41.85,
            "longitude": -87.65,
            "timezone": "America/Chicago",
        }
    ]
}
CURRENT: dict[str, object] = {
    "time": "2026-09-21T05:00",
    "temperature_2m": 15.6,
    "relative_humidity_2m": 81,
    "wind_speed_10m": 28.5,
    "weather_code": 3,
}
FC: dict[str, object] = {
    "current": {
        "time": "2026-09-21T05:00",
        "temperature_2m": 15.6,
        "relative_humidity_2m": 81,
        "wind_speed_10m": 28.5,
        "weather_code": 3,
    },
    "daily": {
        "time": ["2026-09-21", "2026-09-22"],
        "temperature_2m_max": [22.1, 19.0],
        "temperature_2m_min": [12.4, 11.0],
        "precipitation_sum": [0.0, None],
    },
}


def fake(url: str, params: dict[str, str]) -> dict[str, object]:
    if url == GEOCODE_URL:
        assert params["name"] == "Chicago"
        return GEO
    assert url == FORECAST_URL and params["forecast_days"] == "2"
    return FC


def test_geocode_and_forecast_parse_recorded_responses() -> None:
    place = geocode("  Chicago ", fake)
    assert place == Place("Chicago", "United States", 41.85, -87.65, "America/Chicago")
    r = forecast(place, 2, fake)
    assert r.temperature_c == 15.6 and r.humidity_pct == 81 and r.condition == "overcast"
    assert [d.high_c for d in r.days] == [22.1, 19.0]
    assert r.days[1].precipitation_mm == 0.0  # null precipitation becomes 0
    text = format_report(r)
    assert text.splitlines()[0].startswith(
        "Chicago, United States (41.85, -87.65) at 2026-09-21T05:00"
    )
    assert "now: 16°C, overcast, humidity 81%, wind 28 km/h" in text
    assert "2026-09-22: high 19°C, low 11°C, precipitation 0.0 mm" in text
    f = format_report(r, fahrenheit=True)
    assert "now: 60°F" in f
    assert c_to_f(100) == 212


def test_rejections() -> None:
    with pytest.raises(ValueError, match="blank"):
        geocode("  ", fake)
    with pytest.raises(LookupError, match="no place"):
        geocode("Nowhere", lambda _u, _p: {"results": []})
    with pytest.raises(ValueError, match="unexpected geocoding"):
        geocode("x", lambda _u, _p: {"results": ["bad"]})
    place = Place("P", "C", 0, 0, "UTC")
    with pytest.raises(ValueError, match="days"):
        forecast(place, 0, fake)
    with pytest.raises(ValueError, match="missing"):
        forecast(place, 1, lambda _u, _p: {"current": {}})
    with pytest.raises(ValueError, match="malformed"):
        forecast(
            place,
            1,
            lambda _u, _p: {
                "current": FC["current"],
                "daily": {
                    "time": "x",
                    "temperature_2m_max": [],
                    "temperature_2m_min": [],
                    "precipitation_sum": [],
                },
            },
        )
    with pytest.raises(ValueError, match="differ"):
        forecast(
            place,
            1,
            lambda _u, _p: {
                "current": FC["current"],
                "daily": {
                    "time": ["a"],
                    "temperature_2m_max": [],
                    "temperature_2m_min": [],
                    "precipitation_sum": [],
                },
            },
        )
    current = dict(CURRENT)
    current["weather_code"] = 42
    unknown = forecast(place, 1, lambda _u, _p: {"current": current, "daily": FC["daily"]})
    assert unknown.condition == "WMO code 42"


def test_http_get_json_uses_requests(monkeypatch: pytest.MonkeyPatch) -> None:
    import requests

    from pyutils import weather

    class Resp:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> object:
            return {"ok": True}

    monkeypatch.setattr(requests, "get", lambda *_a, **_k: Resp())
    assert weather.http_get_json("u", {}) == {"ok": True}

    class Bad(Resp):
        def json(self) -> object:
            return []

    monkeypatch.setattr(requests, "get", lambda *_a, **_k: Bad())
    with pytest.raises(ValueError, match="shape"):
        weather.http_get_json("u", {})
