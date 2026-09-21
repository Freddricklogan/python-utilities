"""Weather lookup through the Open-Meteo geocoding and forecast APIs (no key). The HTTP call is an
injected function so the parsing and formatting are tested on recorded responses."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import requests

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
TIMEOUT = 15
Fetcher = Callable[[str, dict[str, str]], dict[str, object]]

WMO = {
    0: "clear sky",
    1: "mainly clear",
    2: "partly cloudy",
    3: "overcast",
    45: "fog",
    48: "depositing rime fog",
    51: "light drizzle",
    53: "drizzle",
    55: "dense drizzle",
    61: "slight rain",
    63: "rain",
    65: "heavy rain",
    71: "slight snow",
    73: "snow",
    75: "heavy snow",
    80: "rain showers",
    81: "moderate rain showers",
    82: "violent rain showers",
    95: "thunderstorm",
    96: "thunderstorm with hail",
    99: "thunderstorm with heavy hail",
}


def http_get_json(url: str, params: dict[str, str]) -> dict[str, object]:
    r = requests.get(url, params=params, timeout=TIMEOUT, headers={"User-Agent": "pyutils/1.0"})
    r.raise_for_status()
    data = r.json()
    if not isinstance(data, dict):
        msg = "unexpected response shape"
        raise ValueError(msg)
    return data


@dataclass(frozen=True)
class Place:
    name: str
    country: str
    latitude: float
    longitude: float
    timezone: str


@dataclass(frozen=True)
class Day:
    date: str
    high_c: float
    low_c: float
    precipitation_mm: float


@dataclass(frozen=True)
class Report:
    place: Place
    time: str
    temperature_c: float
    humidity_pct: int
    wind_kmh: float
    condition: str
    days: list[Day]


def geocode(name: str, fetch: Fetcher = http_get_json) -> Place:
    if not name.strip():
        msg = "place name must not be blank"
        raise ValueError(msg)
    data = fetch(
        GEOCODE_URL, {"name": name.strip(), "count": "1", "language": "en", "format": "json"}
    )
    results = data.get("results")
    if not isinstance(results, list) or not results:
        msg = f"no place found for {name!r}"
        raise LookupError(msg)
    r = results[0]
    if not isinstance(r, dict):
        msg = "unexpected geocoding result"
        raise ValueError(msg)
    return Place(
        name=str(r.get("name", name)),
        country=str(r.get("country", r.get("country_code", ""))),
        latitude=float(r["latitude"]),
        longitude=float(r["longitude"]),
        timezone=str(r.get("timezone", "UTC")),
    )


def forecast(place: Place, days: int = 3, fetch: Fetcher = http_get_json) -> Report:
    if not 1 <= days <= 16:
        msg = "days must be 1-16"
        raise ValueError(msg)
    data = fetch(
        FORECAST_URL,
        {
            "latitude": f"{place.latitude:.4f}",
            "longitude": f"{place.longitude:.4f}",
            "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code",
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
            "forecast_days": str(days),
            "timezone": "auto",
        },
    )
    cur = data.get("current")
    daily = data.get("daily")
    if not isinstance(cur, dict) or not isinstance(daily, dict):
        msg = "forecast response missing current or daily blocks"
        raise ValueError(msg)
    dates = daily["time"]
    highs = daily["temperature_2m_max"]
    lows = daily["temperature_2m_min"]
    rain = daily["precipitation_sum"]
    if not (
        isinstance(dates, list)
        and isinstance(highs, list)
        and isinstance(lows, list)
        and isinstance(rain, list)
    ):
        msg = "daily block malformed"
        raise ValueError(msg)
    if not len(dates) == len(highs) == len(lows) == len(rain):
        msg = "daily arrays differ in length"
        raise ValueError(msg)
    code = int(cur["weather_code"])
    return Report(
        place=place,
        time=str(cur["time"]),
        temperature_c=float(cur["temperature_2m"]),
        humidity_pct=int(cur["relative_humidity_2m"]),
        wind_kmh=float(cur["wind_speed_10m"]),
        condition=WMO.get(code, f"WMO code {code}"),
        days=[
            Day(str(d), float(h), float(lo), float(p or 0))
            for d, h, lo, p in zip(dates, highs, lows, rain, strict=True)
        ],
    )


def c_to_f(c: float) -> float:
    return c * 9 / 5 + 32


def format_report(r: Report, fahrenheit: bool = False) -> str:
    conv = c_to_f if fahrenheit else (lambda x: x)
    unit = "°F" if fahrenheit else "°C"
    where = f"{r.place.name}, {r.place.country} ({r.place.latitude:.2f}, {r.place.longitude:.2f})"
    lines = [
        f"{where} at {r.time} {r.place.timezone}",
        f"now: {conv(r.temperature_c):.0f}{unit}, {r.condition}, humidity {r.humidity_pct}%, "
        f"wind {r.wind_kmh:.0f} km/h",
    ]
    for d in r.days:
        lines.append(
            f"{d.date}: high {conv(d.high_c):.0f}{unit}, low {conv(d.low_c):.0f}{unit}, "
            f"precipitation {d.precipitation_mm:.1f} mm"
        )
    return "\n".join(lines)
