import pytest
from aeris_langchain.client import AerisClient


@pytest.fixture
def client():
    return AerisClient(api_key="TEST", endpoint="http://localhost:8000/graphql")


def test_execute_query(client):
    # Mock query for testing
    query = """
    query {
        me {
            id
            username
            email
        }
    }
    """
    # Assuming a mock response for testing purposes
    response = client.execute_query(query)
    assert "me" in response
    assert "id" in response["me"]
    assert "username" in response["me"]


def test_execute_mutation(client):
    # Mock mutation for testing
    mutation = """
    mutation CreateProject($name: String!, $description: String) {
        createProject(name: $name, description: $description) {
            id
            name
            description
        }
    }
    """
    variables = {"name": "Test Project", "description": "A project for testing"}
    response = client.execute_mutation(mutation, variables)
    assert "createProject" in response
    assert response["createProject"]["name"] == "Test Project"
