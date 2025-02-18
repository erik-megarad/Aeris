import logging
import os
import subprocess
import sys
import time
from asyncio import get_event_loop_policy

import httpx
import pytest
import pytest_asyncio

from aeris.db import refresh_db
from aeris.env import env

env()

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(message)s",  # Use only the message to preserve line breaks
)

PORT = os.environ.get("PORT", 8001)


@pytest_asyncio.fixture(scope="function", autouse=True)
async def clean_database():
    await refresh_db()


@pytest.fixture(scope="session", autouse=True)
def graphql_server():
    """
    Start the GraphQL server in the background for the duration of the test session.
    """
    # Start the server
    server_process = subprocess.Popen(
        ["uvicorn", "aeris.main:app", "--port", PORT],
        stdout=sys.stdout,
        stderr=sys.stderr,
    )
    time.sleep(1.5)

    # Wait for the server to start by polling the port
    start_time = time.time()
    while time.time() - start_time < 5:
        try:
            httpx.get(f"http://localhost:{PORT}")
            break
        except httpx.RequestError:
            logger.exception("Server not started yet")
            time.sleep(0.1)
    else:
        raise Exception("Server did not start in time")

    # Yield control to the tests
    yield

    # Teardown: Stop the server
    server_process.terminate()
    server_process.wait()


@pytest_asyncio.fixture(scope="session", autouse=True)
def event_loop(request):
    """Create an instance of the default event loop for each test case."""
    loop = get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
