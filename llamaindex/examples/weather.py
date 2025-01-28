import os
import re
from datetime import datetime, tzinfo

import httpx
import pytz  # type: ignore
from dotenv import load_dotenv
from llama_index.core.agent.workflow import (
    AgentInput,
    AgentOutput,
    AgentStream,
    AgentWorkflow,
    FunctionAgent,
    ToolCall,
    ToolCallResult,
)
from llama_index.core.workflow import Context
from llama_index.llms.openai import OpenAI
from tavily import AsyncTavilyClient  # type: ignore

load_dotenv()


async def search_web(query: str) -> str:
    """Useful for using the web to answer questions."""
    client = AsyncTavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    return str(await client.search(query))


def extract_floats(input_string: str) -> list[float]:
    # Regex to match floats, including negative numbers
    float_pattern = r"-?\d+\.\d+"
    # Find all matches in the input string
    matches = re.findall(float_pattern, input_string)
    # Convert matches to floats
    return [float(match) for match in matches]


async def lookup_location(ctx: Context, latitude_and_longitude: str) -> str:
    """Useful for recording the latitude and longitude of a given location. Your input should be the latitude and longitude of the location."""
    current_state = await ctx.get("state")
    lat, lon = extract_floats(latitude_and_longitude)
    current_state["lat"] = lat
    current_state["lon"] = lon
    return f"Latitude ({lat}) and longitude ({lon}) written."


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
        forecast_string += f"""## {datetime.fromtimestamp(hour["dt"], tz=timezone).strftime("%Y-%m-%d %H")}
{format_weather_datum(hour, unit, timezone)}"""

    forecast_string += "# Daily Forecast\n"
    for day in data["daily"]:
        forecast_string += f"""## {datetime.fromtimestamp(day["dt"], tz=timezone).strftime("%Y-%m-%d")}
{format_weather_datum(day, unit, timezone)}"""

    current_state = await ctx.get("state")
    current_state["forecast"] = forecast_string
    await ctx.set("state", current_state)

    return f"Weather forecast is ready.\n{forecast_string}"


async def record_analysis(ctx: Context, analysis: str) -> str:
    """Useful for recording your analysis of a weather report."""
    current_state = await ctx.get("state")
    current_state["analysis"] = analysis
    await ctx.set("state", current_state)
    return "Weather analyzed.\n{analysis}"


async def record_analysis_review(ctx: Context, review: str, accepted: bool) -> str:
    """Useful for recording the outcome of a review of a weather analysis, determining if it conforms strictly to the original report."""
    current_state = await ctx.get("state")
    current_state["review"] = review
    await ctx.set("state", current_state)
    if not accepted:
        return "Changes requested."
    return "Analysis approved."


llm = OpenAI(model="gpt-4o-mini", api_key=os.getenv("OPENAI_API_KEY"))

lookup_agent = FunctionAgent(
    name="WeatherLookupAgent",
    description="Useful for retrieving a weather forecast.",
    system_prompt=(
        "You are the WeatherLookupAgent that can look up information using the OpenWeatherMap API. "
        "Once the weather forecast has been retrieved, you should hand off control to the WeatherAnalysisAgent for analysis."
    ),
    llm=llm,
    tools=[lookup_location, guess_unit_of_measurement, lookup_weather],  # type: ignore
    can_handoff_to=["WeatherAnalysisAgent"],
)

write_agent = FunctionAgent(
    name="WeatherAnalysisAgent",
    description="Useful for writing a report on a given topic.",
    system_prompt=(
        "You are the WeatherAnalysisAgent that can write an analysis of weather forecast. "
        "Your analysis should be in the style of a script for a two-minute video presentation. "
        "People will be relying on the accuracy of the forecast, so ensure that the content is grounded in the provided forecast. "
        "Once the analysis is complete, you should get feedback at least once from the WeatherAnalysisReviewerAgent."
    ),
    llm=llm,
    tools=[search_web, record_analysis],  # type: ignore
    can_handoff_to=["WeatherAnalysisReviewerAgent"],
)

review_agent = FunctionAgent(
    name="WeatherAnalysisReviewerAgent",
    description="Useful for reviewing a report and providing feedback.",
    system_prompt=(
        "You are the WeatherAnalysisReviewerAgent that reviews weather forecast analysis for accuracy. Your goal is to ensure that the analysis is grounded in the provided forecast. "
        "Your review should either approve the current report or request changes for the WeatherAnalysisAgent to implement. "
        "If you have feedback that requires changes, you should hand off control to the WeatherAnalysisAgent to implement the changes after submitting the review."
    ),
    llm=llm,
    tools=[record_analysis_review],  # type: ignore
    can_handoff_to=["WeatherAnalysisAgent"],
)

agent_workflow = AgentWorkflow(
    agents=[lookup_agent, write_agent, review_agent],
    root_agent="WeatherLookupAgent",
    initial_state={
        "forecast": "",
        "analysis": "",
        "review": "",
        "lat": 0,
        "lon": 0,
    },
    state_prompt="Current state: {state}. User message: {msg}",
)


async def main():
    location = input("Enter a location: ")
    handler = agent_workflow.run(
        user_msg=f"Get the weather forecast for {location}.",
    )

    current_agent = None
    async for event in handler.stream_events():
        if (
            hasattr(event, "current_agent_name")
            and event.current_agent_name != current_agent
        ):
            current_agent = event.current_agent_name
            print(f"\n{'='*50}")
            print(f"🤖 Agent: {current_agent}")
            print(f"{'='*50}\n")
        elif isinstance(event, AgentStream):
            if event.delta:
                print(event.delta, end="", flush=True)
        elif isinstance(event, AgentInput):
            print("📥 Input:", event.input)
        elif isinstance(event, AgentOutput):
            if event.response.content:
                print("📤 Output:", event.response.content)
            if event.tool_calls:
                print(
                    "🛠️  Planning to use tools:",
                    [call.tool_name for call in event.tool_calls],
                )
        elif isinstance(event, ToolCallResult):
            print(f"🔧 Tool Result ({event.tool_name}):")
            print(f"  Arguments: {event.tool_kwargs}")
            print(f"  Output: {event.tool_output}")
        elif isinstance(event, ToolCall):
            print(f"🔨 Calling Tool: {event.tool_name}")
            print(f"  With arguments: {event.tool_kwargs}")

    state = await handler.ctx.get("state")
    print(state["analysis"])


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
