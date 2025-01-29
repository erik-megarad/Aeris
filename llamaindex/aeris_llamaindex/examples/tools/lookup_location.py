import re

from dotenv import load_dotenv
from llama_index.core.workflow import Context

load_dotenv()


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
