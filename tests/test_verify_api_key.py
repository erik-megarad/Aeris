import os

import httpx
import pytest
from bcrypt import gensalt, hashpw

from aeris.db import DB
from aeris.env import env

env()
port = os.environ.get("PORT", 8001)
GRAPHQL_URL = f"http://localhost:{port}/graphql"


# Test API key authentication
@pytest.mark.asyncio
async def test_api_key_auth():
    headers = {"Authorization": "Bearer TEST"}
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
async def test_api_key_missing():
    test_api_key = "TEST_INVALID"

    headers = {"Authorization": f"Bearer {test_api_key}"}
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
        assert response.status_code == 401

        data = response.json()
        assert "errors" in data
        assert data["errors"][0]["message"] == "Authentication failed: Invalid API key"


@pytest.mark.asyncio
async def test_api_key_invalid():
    test_api_key = "TEST_INVALID"
    async with DB() as conn:
        hashed_api_key = hashpw(test_api_key.encode(), gensalt())
        await conn.execute(
            "INSERT INTO api_keys (user_id, project_id, key, active) VALUES (1, 1, $1, false);",
            hashed_api_key.decode(),
        )

    headers = {"Authorization": f"Bearer {test_api_key}"}
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
        assert response.status_code == 401

        data = response.json()
        assert "errors" in data
        assert data["errors"][0]["message"] == "Authentication failed: Invalid API key"


@pytest.mark.asyncio
async def test_api_key_expired():
    test_api_key = "TEST_INVALID"
    async with DB() as conn:
        hashed_api_key = hashpw(test_api_key.encode(), gensalt())
        await conn.execute(
            "INSERT INTO api_keys (user_id, project_id, key, expires_at) VALUES (1, 1, $1, NOW());",
            hashed_api_key.decode(),
        )

    headers = {"Authorization": f"Bearer {test_api_key}"}
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
        assert response.status_code == 401

        data = response.json()
        assert "errors" in data
        assert data["errors"][0]["message"] == "Authentication failed: Invalid API key"
