from ariadne import QueryType

from aeris.data.project import get_project_by_uuid, get_projects, get_tasks_for_project
from aeris.data.task import get_task_by_uuid
from aeris.data.user import get_user_by_id

query = QueryType()


# Example User resolver
@query.field("me")
async def resolve_me(_, info):
    user_id = info.context["user_id"]
    user = dict(await get_user_by_id(user_id))
    user.pop("id")
    return user


# Projects resolver
@query.field("projects")
async def resolve_projects(_, info, pagination=None):
    user_id = info.context["user_id"]
    projects = [dict(project) for project in await get_projects(user_id, pagination)]
    [project.pop("id") for project in projects]
    return projects


# Single Project resolver
@query.field("project")
async def resolve_project(_, info, uuid):
    user_id = info.context["user_id"]
    project = dict(await get_project_by_uuid(uuid, user_id))

    if not project:
        return None

    project.pop("id")
    return project


# Tasks resolver
@query.field("tasks")
async def resolve_tasks(_, info, projectId, pagination=None, filters=None):
    user_id = info.context["user_id"]
    tasks = [dict(task) for task in await get_tasks_for_project(projectId, user_id, pagination, filters)]
    [task.pop("id") for task in tasks]
    edges = [{"cursor": task["uuid"], "node": task} for task in tasks]
    return {"edges": edges, "pageInfo": {"hasNextPage": False, "hasPreviousPage": False}}


# Single Task resolver
@query.field("task")
async def resolve_task(_, info, uuid):
    user_id = info.context["user_id"]
    task = dict(await get_task_by_uuid(uuid, user_id))
    task.pop("id")
    return task
