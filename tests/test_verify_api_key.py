import os

import httpx
import pytest

from aeris.env import env

env()
port = os.environ.get("PORT", 8001)
GRAPHQL_URL = f"http://localhost:{port}/graphql"


# Test API key authentication
@pytest.mark.asyncio
async def test_api_key_auth():
    headers = {"Authorization": "Bearer test-api-key"}
    query = """
    query {
        projects {
            id
            name
        }
    }
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(GRAPHQL_URL, json={"query": query}, headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert "errors" not in data
        assert len(data["data"]["projects"]) == 1
        assert data["data"]["projects"][0]["name"] == "Test Project"


# Test API key invalidation
@pytest.mark.asyncio
async def test_api_key_invalid():
    headers = {"Authorization": "Bearer invalid-key"}
    query = """
    query {
        projects {
            id
            name
        }
    }
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(GRAPHQL_URL, json={"query": query}, headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert "errors" in data
        assert data["errors"][0]["message"] == "Authentication failed: Invalid API key"
