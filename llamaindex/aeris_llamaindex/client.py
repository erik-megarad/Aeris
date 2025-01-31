import os
from typing import Any, Dict, Optional

from gql import Client, gql
from gql.transport.httpx import HTTPXAsyncTransport
from llama_index.core.agent.workflow import (
    AgentStream,
)
from llama_index.core.workflow.events import Event

DEFAULT_ENDPOINT = "http://localhost:8000/graphql"


class AerisClient:
    """
    A client for interacting with the Aeris GraphQL API.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        project_id: Optional[str] = None,
        task_id: Optional[str] = None,
    ):
        """
        Initialize the Aeris GraphQL client.

        Args:
            api_key (str): API key for authenticating requests.
            endpoint (str): The GraphQL API endpoint. Defaults to the production URL.
        """
        self.task_id = task_id
        endpoint = endpoint or os.getenv("AERIS_API_ENDPOINT") or DEFAULT_ENDPOINT

        project_id = project_id or os.getenv("AERIS_PROJECT_ID")
        if not project_id:
            raise ValueError(
                "You must provide a project ID. Create a project in Aeris and set the ID."
            )
        self.project_id = project_id

        api_key = api_key or os.getenv("AERIS_API_KEY")

        if not api_key:
            raise ValueError("API key is required to interact with the Aeris API.")

        self.transport = HTTPXAsyncTransport(
            url=endpoint, headers={"Authorization": f"Bearer {api_key}"}
        )
        self.client = Client(transport=self.transport, fetch_schema_from_transport=True)

    async def execute_query(
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
            return await self.client.execute_async(gql_query, variable_values=variables)
        except Exception as e:
            raise RuntimeError(f"Error executing query: {str(e)}")

    async def execute_mutation(
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
            return await self.client.execute_async(
                gql_mutation, variable_values=variables
            )
        except Exception as e:
            raise RuntimeError(f"Error executing mutation: {str(e)}")

    async def fetch_similar_tasks(
        self, task_input: Optional[str] = None, embedding: Optional[list[float]] = None
    ) -> list[str]:
        """
        Fetch similar tasks from Aeris.

        Args:
            task_input (Optional[str]): Text input to search for similar tasks.
            embedding (Optional[List[float]]): Embedding to search for similar tasks.

        Returns:
            List[Dict[str, Any]]: A list of similar tasks with similarity scores.
        """
        if not task_input and not embedding:
            raise ValueError("You must provide either 'task_input' or 'embedding'.")

        query = """query FindSimilarTasks($input: String) {
  findSimilarTasks(input: $input) {
    similarity
    task {
      id
      name
      input
      state
      success
      feedback
      events {
        edges {
          node {
            eventType
            eventData
          }
        }
      }
    }
  }
}"""

        variables = {"input": task_input}
        response = await self.execute_query(query, variables)

        similar_tasks = []
        for similarity in response["findSimilarTasks"]:
            task = similarity["task"]
            task_summary = f"""# Similar Task: {task['name']}
Task Input: {task['input']}
State: {task['state']}
Success: {task['success']}
Human Feedback: {task['feedback']}

"""
            # for event in task["events"]["edges"]:
            #    task_summary += (
            #        f"  - {event['node']['eventType']}: {event['node']['eventData']}\n"
            #    )

            similar_tasks.append(task_summary)

        return similar_tasks

    async def register_task(self, name: str, task_input: str) -> str:
        """
        Register a task with Aeris.

        Args:
            name (str): The name of the task.
            task_input (str): The input for the task.

        Returns:
            str: The ID of the created task.
        """
        mutation = """
        mutation CreateTask($projectId: ID!, $name: String!, $input: String!) {
            createTask(projectId: $projectId, name: $name, input: $input) {
                id
            }
        }
        """
        variables = {"projectId": self.project_id, "name": name, "input": task_input}
        response = await self.execute_mutation(mutation, variables)
        self.task_id = response["createTask"]["id"]
        if not self.task_id:
            raise ValueError(f"Failed to create task: {response}")

        return self.task_id

    async def log_event(self, event_type: str, event_data: Dict[str, Any]) -> str:
        """
        Log an event for a task in Aeris.

        Args:
            task_id (str): The UUID of the task to log the event for.
            event_type (str): The type of the event.
            event_data (Dict[str, Any]): Data associated with the event.

        Returns:
            str: The ID of the logged event.
        """
        mutation = """
        mutation LogEvent($taskId: ID!, $eventType: String!, $eventData: JSON!) {
            logEvent(taskId: $taskId, eventType: $eventType, eventData: $eventData) {
                id
            }
        }
        """
        variables = {
            "taskId": self.task_id,
            "eventType": event_type,
            "eventData": event_data,
        }
        response = await self.execute_mutation(mutation, variables)
        return response["logEvent"]["id"]

    async def log_llama_event(self, event: Event):
        """
        Log a LlamaIndex workflow event as an Aeris event

        Args:
            event (Event): The LlamaIndex workflow event to log.
        """

        if isinstance(event, AgentStream):
            return

        event_data = event.model_dump()
        event_type = event.__class__.__name__

        return await self.log_event(event_type, event_data)

    async def end_task(self, success: bool, feedback: str) -> str:
        """
        End a task in Aeris. This is typically called when the task is complete or failed.

        Args:
            success (bool): Whether the task was successfully completed.
            feedback (str): Human feedback on the task execution.
        """

        mutation = """
        mutation EndTask($taskId: ID!, $success: Boolean!, $feedback: String!, status: TaskState!) {
            updateTask(id: $taskId, success: $success, feedback: $feedback, status: status) {
                id
            }
        }
        """
        variables = {
            "taskId": self.task_id,
            "success": success,
            "feedback": feedback,
            "status": "SUCCESS" if success else "FAILURE",
        }
        response = await self.execute_mutation(mutation, variables)
        return response["updateTask"]["id"]
