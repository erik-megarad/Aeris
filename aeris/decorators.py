from typing import Any

from asyncpg import Record


def decorate_task(task: Record) -> dict[str, Any]:
    task_dict = dict(task)
    task_dict["id"] = task_dict.pop("uuid")
    return task_dict


def decorate_project(project: Record) -> dict[str, Any]:
    project_dict = dict(project)
    project_dict["id"] = project_dict.pop("uuid")
    return project_dict


def decorate_user(user: Record) -> dict[str, Any]:
    user_dict = dict(user)
    user_dict["id"] = user_dict.pop("uuid")
    return user_dict
