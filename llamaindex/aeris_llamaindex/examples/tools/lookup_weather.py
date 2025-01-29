import os
from datetime import datetime, tzinfo

import httpx
import pytz  # type: ignore
from dotenv import load_dotenv
from llama_index.core.workflow import Context

load_dotenv()


async def guess_unit_of_measurement(ctx: Context, unit: str) -> str:
    """Useful for guessing the unit of measurement based on the given location information. Your input should be one of "metric" or "imperial"."""
    current_state = await ctx.get("state")
    current_state["unit"] = unit
    await ctx.set("state", current_state)
    return f"Unit of measurement guessed as {unit}."


def format_weather_datum(data: dict, unit: str, tz: tzinfo) -> str:
    """Format a weather data dictionary into a human-readable string."""
    temp_abbr = "°F" if unit == "imperial" else "°C"
    speed_abbr = "mph" if unit == "imperial" else "m/s"
    report = f"""- Weather: {data["weather"][0]["description"]}
- Temperature: {data["temp"]}{temp_abbr}
- Feels like: {data["feels_like"]}{temp_abbr}
- Humidity: {data["humidity"]}
- Wind speed: {data["wind_speed"]}{speed_abbr}
- Wind direction: {data["wind_deg"]}
- UV index: {data["uvi"]}"""

    if "visibility" in data:
        report += f"\n- Visibility: {data['visibility']}"

    if "sunrise" in data and "sunset" in data:
        sunrise_time = datetime.fromtimestamp(data["sunrise"], tz=tz).strftime(
            "%H:%M:%S"
        )
        sunset_time = datetime.fromtimestamp(data["sunset"], tz=tz).strftime("%H:%M:%S")
        report += f"\n- Sunrise: {sunrise_time}"
        report += f"\n- Sunset: {sunset_time}"

    return report


OWM_URI = "https://api.openweathermap.org/data/3.0/onecall"


async def lookup_weather(ctx: Context, lat: float, lon: float, unit: str) -> str:
    """Useful for looking up the weather in a given location (latitude and longitude). Unit of measure (either imperial or metric) should be provided."""

    owm_api_key = os.getenv("OWM_API_KEY")
    params = httpx.QueryParams(
        {
            "lat": lat,
            "lon": lon,
            "exclude": "minutely",
            "appid": owm_api_key,
            "units": unit,
        }
    )
    response = httpx.get(OWM_URI, params=params)
    data = response.json()
    timezone = pytz.timezone(data["timezone"])

    forecast_string = f"""# Current Weather
{format_weather_datum(data["current"], unit, timezone)}

# Hourly Forecast
"""
    for hour in data["hourly"]:
        forecast_string += f"""\n\n## Forecast for the hour of {datetime.fromtimestamp(hour["dt"], tz=timezone).strftime("%Y-%m-%d %H")}
{format_weather_datum(hour, unit, timezone)}"""

    forecast_string += "\n\n# Daily Forecast\n"
    for day in data["daily"]:
        forecast_string += f"""\n\n## Forecast for the day of {datetime.fromtimestamp(day["dt"], tz=timezone).strftime("%A, %Y-%m-%d")}
{format_weather_datum(day, unit, timezone)}"""

    current_state = await ctx.get("state")
    current_state["forecast"] = forecast_string
    await ctx.set("state", current_state)

    return f"Weather forecast is ready.\n{forecast_string}"
