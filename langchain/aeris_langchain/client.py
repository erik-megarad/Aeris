import os
from typing import Any, Dict, Optional

from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport

DEFAULT_ENDPOINT = "http://localhost:8000/graphql"


class AerisClient:
    """
    A client for interacting with the Aeris GraphQL API.
    """

    def __init__(self, api_key: Optional[str] = None, endpoint: Optional[str] = None):
        """
        Initialize the Aeris GraphQL client.

        Args:
            api_key (str): API key for authenticating requests.
            endpoint (str): The GraphQL API endpoint. Defaults to the production URL.
        """
        api_key = api_key or os.getenv("AERIS_API_KEY")
        endpoint = endpoint or os.getenv("AERIS_API_ENDPOINT") or DEFAULT_ENDPOINT
        self.transport = RequestsHTTPTransport(
            url=endpoint, headers={"Authorization": f"Bearer {api_key}"}
        )
        self.client = Client(transport=self.transport, fetch_schema_from_transport=True)

    def execute_query(
        self, query: str, variables: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a GraphQL query.

        Args:
            query (str): The GraphQL query string.
            variables (Optional[Dict[str, Any]]): Variables to pass with the query.

        Returns:
            Dict[str, Any]: The response from the API.
        """
        try:
            gql_query = gql(query)
            return self.client.execute(gql_query, variable_values=variables)
        except Exception as e:
            raise RuntimeError(f"Error executing query: {str(e)}")

    def execute_mutation(
        self, mutation: str, variables: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a GraphQL mutation.

        Args:
            mutation (str): The GraphQL mutation string.
            variables (Optional[Dict[str, Any]]): Variables to pass with the mutation.

        Returns:
            Dict[str, Any]: The response from the API.
        """
        try:
            gql_mutation = gql(mutation)
            return self.client.execute(gql_mutation, variable_values=variables)
        except Exception as e:
            raise RuntimeError(f"Error executing mutation: {str(e)}")
