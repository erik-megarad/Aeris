import os

import httpx
import pytest

from aeris.env import env

env()
port = os.environ.get("PORT", 8001)
GRAPHQL_URL = f"http://localhost:{port}/graphql"


@pytest.mark.asyncio
async def test_get_task_by_uuid():
    query = """
    query {
      task(id:"123e4567-e89b-12d3-a456-426614174000"){
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
        assert "task" in data["data"]
        assert data["data"]["task"]["name"] == "Test Task"
        assert data["data"]["task"]["id"] == "123e4567-e89b-12d3-a456-426614174000"


@pytest.mark.asyncio
async def test_get_tasks_for_project():
    query = """
    query {
      tasks(projectId:"36e8705e-6604-4e44-b58f-4e8c347a9f31") {
        edges {
          node {
            id
            name
          }
        }
      }
    }
    """
    headers = {"Authorization": "Bearer TEST"}
    async with httpx.AsyncClient() as client:
        response = await client.post(GRAPHQL_URL, json={"query": query}, headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert "data" in data
        assert "tasks" in data["data"]
        assert len(data["data"]["tasks"]["edges"]) == 1
        tasks_data = [datum["node"] for datum in data["data"]["tasks"]["edges"]]
        assert tasks_data[0]["name"] == "Test Task"
        assert tasks_data[0]["id"] == "123e4567-e89b-12d3-a456-426614174000"


@pytest.mark.asyncio
async def test_create_task():
    query = """
    mutation {
      createTask(projectId:"36e8705e-6604-4e44-b58f-4e8c347a9f31", name: "New Task", input: "Test Input") {
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
        assert "createTask" in data["data"]
        assert data["data"]["createTask"]["name"] == "New Task"
        assert data["data"]["createTask"]["id"] is not None
