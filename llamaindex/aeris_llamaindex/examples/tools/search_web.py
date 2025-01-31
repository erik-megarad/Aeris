import os

from dotenv import load_dotenv
from llama_index.core.tools import FunctionTool
from tavily import AsyncTavilyClient  # type: ignore

load_dotenv()


async def search_web_fn(query: str) -> str:
    """Useful for using the web to answer questions."""
    client = AsyncTavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    return str(await client.search(query))


search_web = FunctionTool.from_defaults(search_web_fn)
