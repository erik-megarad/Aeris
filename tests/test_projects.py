import os

import httpx
import pytest

from aeris.db import DB
from aeris.env import env

env()
port = os.environ.get("PORT", 8001)
GRAPHQL_URL = f"http://localhost:{port}/graphql"


@pytest.mark.asyncio
async def test_list_projects():
    query = """
    query {
        projects {
            id
            name
        }
    }
    """
    headers = {"Authorization": "Bearer TEST"}
    async with httpx.AsyncClient() as client:
        response = await client.post(GRAPHQL_URL, json={"query": query}, headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert "data" in data
        assert "projects" in data["data"]
        assert len(data["data"]["projects"]) == 1
        assert data["data"]["projects"][0]["name"] == "Test Project"
        assert data["data"]["projects"][0]["id"] == "36e8705e-6604-4e44-b58f-4e8c347a9f31"


@pytest.mark.asyncio
async def test_create_project():
    query = """
    mutation {
        createProject(name: "New Project") {
            id
            name
        }
    }
    """
    headers = {"Authorization": "Bearer TEST"}
    async with httpx.AsyncClient() as client:
        response = await client.post(GRAPHQL_URL, json={"query": query}, headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert data.get("data") is not None
        assert "createProject" in data["data"]
        assert data["data"]["createProject"]["name"] == "New Project"
        assert data["data"]["createProject"]["id"] is not None

    async with DB() as conn:
        project = await conn.fetchrow("SELECT * FROM projects WHERE name = $1", "New Project")
        assert project is not None
        assert project["name"] == "New Project"
