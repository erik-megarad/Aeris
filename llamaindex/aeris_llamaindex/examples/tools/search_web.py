import os

from dotenv import load_dotenv
from tavily import AsyncTavilyClient  # type: ignore

load_dotenv()


async def search_web(query: str) -> str:
    """Useful for using the web to answer questions."""
    client = AsyncTavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    return str(await client.search(query))
