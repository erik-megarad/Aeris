import os
from typing import Any, Dict, List, Optional
from langchain_core.runnables.config import  RunnableConfig
from uuid import UUID

from aeris_langchain.callback_handler import AerisCallbackHandler
from aeris_langchain.client import AerisClient
from aeris_langchain.runnables import EnrichPromptRunnable


class AerisMiddleware:
    """
    Middleware for integrating Aeris functionality into agent workflows.
    """
    task_id: Optional[str] = None
    project_id: str
    client: AerisClient

    def __init__(
        self, project_id: Optional[str] = None, client: Optional[AerisClient] = None
    ):
        """
        Initialize AerisMiddleware.

        Args:
            client (AerisClient): An instance of the Aeris GraphQL client.
            project_id (str): The ID of the Aeris project to interact with.
        """
        project_id = project_id or os.getenv("AERIS_PROJECT_ID")
        if not project_id:
            raise ValueError(
                "You must provide a project ID. Create a project in Aeris and set the ID."
            )
        self.project_id = project_id
        self.client = client or AerisClient()

    def register_task(self, name: str, task_input: str) -> str:
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
        response = self.client.execute_mutation(mutation, variables)
        self.task_id = response["createTask"]["id"]
        if not self.task_id:
            raise ValueError(f"Failed to create task: {response}")

        return self.task_id

    def fetch_similar_tasks(
        self, task_input: Optional[str] = None, embedding: Optional[List[float]] = None
    ) -> List[Dict[str, Any]]:
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

        query = """
        query FindSimilarTasks($input: String) {
            findSimilarTasks(input: $input) {
                task {
                    id
                    name
                    input
                    result
                }
                similarity
            }
        }
        """
        variables = {"input": task_input}
        response = self.client.execute_query(query, variables)
        return response["findSimilarTasks"]

    def enrich_prompt(self, task_input: str, existing_prompt: str) -> str:
        """
        Enrich the agent's prompt with results from similar tasks.

        Args:
            task_input (str): The current task input.
            existing_prompt (str): The agent's current planning prompt.

        Returns:
            str: The enriched prompt with similar tasks' results.
        """
        similar_tasks = self.fetch_similar_tasks(task_input=task_input)
        if not similar_tasks:
            return existing_prompt

        similar_context = "\n".join(
            f"Task: {task['task']['name']}\n"
            f"Input: {task['task']['input']}\n"
            f"Result: {task['task']['result']}\n"
            f"Similarity (euclidean distance): {task['similarity']:.2f}\n"
            for task in similar_tasks
        )

        return f"{existing_prompt}\n\n### Similar Tasks:\nAnalyze lessons from similar tasks to inform your plan. Note: Lower similarity scores indicate closer matches.\n{similar_context}"

    def log_event(
        self, event_type: str, event_data: Dict[str, Any]
    ) -> str:
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
        response = self.client.execute_mutation(mutation, variables)
        breakpoint()
        return response["logEvent"]["id"]
    
    def callback_handler(self):
        return AerisCallbackHandler(self)
    
    def config(self):
        return RunnableConfig(
            callback_handler=self.callback_handler()
        )
    
    def prompt_enrichment_runnable(self):
        return EnrichPromptRunnable(self)
        