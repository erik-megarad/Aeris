from typing import Any

from asyncpg import Record


def decorate_task(task: Record) -> dict[str, Any]:
    task_dict = dict(task)
    task_dict["id"] = task_dict.pop("uuid")
    task_dict["createdAt"] = task_dict["created_at"].isoformat()
    return task_dict


def decorate_task_similarity(task: Record) -> dict[str, Any]:
    task_dict = dict(task)
    similarity = task_dict.pop("similarity_score")
    task_dict["id"] = task_dict.pop("uuid")
    return {"similarity": similarity, "task": task_dict}


def decorate_project(project: Record) -> dict[str, Any]:
    project_dict = dict(project)
    project_dict["id"] = project_dict.pop("uuid")
    return project_dict


def decorate_user(user: Record) -> dict[str, Any]:
    user_dict = dict(user)
    user_dict["id"] = user_dict.pop("uuid")
    return user_dict


def decorate_event(event):
    """
    Transform the raw database event into the GraphQL schema format.
    """
    return {
        "id": event["id"],
        "eventType": event["event_type"],
        "eventData": event["event_data"],
        "createdAt": event["created_at"].isoformat(),
    }
