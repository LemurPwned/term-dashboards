from __future__ import annotations

from typing import Any

import datetime as dt
import requests
from rich.text import Text

from term_dashboard.tiles.base import BaseTile


class WeatherTile(BaseTile):
    tile_name = "weather"
    title = "Weather"

    def __init__(self, config: dict[str, Any], global_config: Any) -> None:
        super().__init__(config, global_config)
        self._geocode_cache: dict[str, tuple[float, float]] = {}

    def fetch_data(self) -> dict[str, Any]:
        city = self.config.get("city")
        if not city:
            raise ValueError("City is required in tile_weather.yml")

        latitude = self.config.get("latitude")
        longitude = self.config.get("longitude")
        if latitude is None or longitude is None:
            latitude, longitude = self._get_location(city)
        units = self.config.get("units", "metric")
        temp_unit = "fahrenheit" if units == "imperial" else "celsius"
        wind_unit = "mph" if units == "imperial" else "kmh"

        response = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": latitude,
                "longitude": longitude,
                "current_weather": "true",
                "daily": "temperature_2m_max,temperature_2m_min,weathercode",
                "temperature_unit": temp_unit,
                "windspeed_unit": wind_unit,
                "timezone": "auto",
            },
            timeout=10,
        )
        response.raise_for_status()
        payload = response.json()
        current = payload.get("current_weather", {})
        daily = payload.get("daily", {})
        forecast_days = int(self.config.get("forecast_days", 5))
        daily_dates = daily.get("time") or []
        daily_highs = daily.get("temperature_2m_max") or []
        daily_lows = daily.get("temperature_2m_min") or []
        daily_codes = daily.get("weathercode") or []

        forecast = []
        for index in range(min(forecast_days, len(daily_dates))):
            forecast.append(
                {
                    "date": daily_dates[index],
                    "high": daily_highs[index] if index < len(daily_highs) else None,
                    "low": daily_lows[index] if index < len(daily_lows) else None,
                    "code": daily_codes[index] if index < len(daily_codes) else None,
                }
            )
        return {
            "city": city,
            "temperature": current.get("temperature"),
            "windspeed": current.get("windspeed"),
            "current_code": current.get("weathercode"),
            "units": units,
            "wind_unit": wind_unit,
            "high": (daily_highs or [None])[0],
            "low": (daily_lows or [None])[0],
            "forecast": forecast,
        }

    def _get_location(self, city: str) -> tuple[float, float]:
        if city in self._geocode_cache:
            return self._geocode_cache[city]

        response = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": city, "count": 1},
            timeout=10,
        )
        response.raise_for_status()
        results = response.json().get("results")
        if not results:
            raise ValueError(f"No results found for {city}")
        location = results[0]
        coords = (location["latitude"], location["longitude"])
        self._geocode_cache[city] = coords
        return coords

    def render_data(self, data: dict[str, Any]) -> None:
        unit_label = "F" if data.get("units") == "imperial" else "C"
        temp = self._format_value(data.get("temperature"), unit_label)
        wind_unit = data.get("wind_unit", "")
        wind_value = data.get("windspeed")
        wind = "—" if wind_value is None else f"{wind_value:.1f} {wind_unit}".strip()
        high = self._format_value(data.get("high"), unit_label)
        low = self._format_value(data.get("low"), unit_label)
        bar = self._temp_bar(data.get("temperature"), data.get("low"), data.get("high"))
        output = Text(data.get("city", ""))
        output.append("\n")
        output.append(f"Now: {temp}  Wind: {wind}")
        output.append("\n")
        output.append(f"Today: H {high} / L {low}")
        output.append("\n")
        output.append(bar)
        art = self._current_art(data.get("current_code"))
        if art:
            output.append("\n")
            output.append(art)
        forecast = self._forecast_chart(data.get("forecast", []), unit_label)
        if forecast:
            output.append("\n")
            output.append(forecast)
        if self.body:
            self.body.update(output)

    @staticmethod
    def _format_value(value: float | None, unit_label: str) -> str:
        if value is None:
            return "—"
        if unit_label:
            return f"{value:.1f}°{unit_label}"
        return f"{value:.1f}"

    @staticmethod
    def _temp_bar(current: float | None, low: float | None, high: float | None) -> Text:
        if current is None or low is None or high is None:
            return Text("Temperature range unavailable", style="dim")
        width = 16
        span = max(high - low, 1e-6)
        position = int(round((current - low) / span * (width - 1)))
        position = max(0, min(position, width - 1))
        text = Text("Temp: ")
        for index in range(width):
            if index == position:
                text.append("█", style="bold yellow")
            elif index < position:
                text.append("█", style="cyan")
            else:
                text.append("█", style="red")
        return text

    def _forecast_chart(self, forecast: list[dict[str, Any]], unit_label: str) -> Text | None:
        if not forecast:
            return None
        highs = [day.get("high") for day in forecast if day.get("high") is not None]
        lows = [day.get("low") for day in forecast if day.get("low") is not None]
        if not highs or not lows:
            return None
        min_temp = min(lows)
        max_temp = max(highs)
        span = max(max_temp - min_temp, 1e-6)
        bar_width = 12

        output = Text("Forecast:\n", style="bold")
        for day in forecast:
            label = self._format_day(day.get("date"))
            day_color = self._day_color(day.get("date"))
            high = day.get("high")
            low = day.get("low")
            if high is None or low is None:
                output.append(Text(f"{label} —", style=day_color))
                output.append("\n")
                continue
            low_pos = int((low - min_temp) / span * (bar_width - 1))
            high_pos = int((high - min_temp) / span * (bar_width - 1))
            bar = Text()
            for index in range(bar_width):
                if low_pos <= index <= high_pos:
                    bar.append("█", style="cyan")
                else:
                    bar.append("░", style="#2a3447")
            temps = f"{low:.1f}/{high:.1f}°{unit_label}"
            line = Text()
            line.append(f"{label} ", style=day_color)
            line.append(bar)
            line.append(f" {temps}")
            output.append(line)
            output.append("\n")
        return output

    def _current_art(self, code: int | None) -> Text | None:
        art = self._weather_art(code)
        if not art:
            return None
        lines, color = art
        block = Text()
        for index, line in enumerate(lines):
            if index:
                block.append("\n")
            block.append(line, style=color)
        return block

    @staticmethod
    def _format_day(date_value: str | None) -> str:
        if not date_value:
            return "---"
        try:
            day = dt.datetime.strptime(date_value, "%Y-%m-%d")
            return day.strftime("%a")
        except ValueError:
            return date_value

    @staticmethod
    def _day_color(date_value: str | None) -> str:
        if not date_value:
            return "white"
        try:
            day = dt.datetime.strptime(date_value, "%Y-%m-%d")
        except ValueError:
            return "white"
        palette = ["cyan", "green", "yellow", "magenta", "blue", "bright_black", "white"]
        return palette[day.weekday() % len(palette)]

    @staticmethod
    def _weather_art(code: int | None) -> tuple[list[str], str] | None:
        if code is None:
            return None
        if code == 0:
            return ([" \ | / ", "  -O-  ", " / | \\"], "yellow")
        if code in (1, 2):
            return (["   .--.", " .(    )", "(___.__)"], "white")
        if code == 3:
            return (["   .--.", " .(____)", "(___.__)"], "bright_black")
        if code in (45, 48):
            return ([" _ - _ ", "  / /  ", " _/ /_ "], "bright_black")
        if code in (51, 53, 55, 56, 57, 61, 63, 65, 80, 81, 82):
            return (["   .--.", " .(    )", "ʻʻʻʻʻʻ"], "blue")
        if code in (66, 67, 71, 73, 75, 77, 85, 86):
            return (["   .--.", " .(    )", " * * *"], "cyan")
        if code in (95, 96, 99):
            return (["   .--.", " .(____)", "  //// "], "magenta")
        return (["   .--.", " .(____)", "  ---- "], "bright_black")
