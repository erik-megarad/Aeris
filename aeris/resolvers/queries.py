from ariadne import QueryType

from aeris.data.project import get_project_by_uuid, get_projects, get_tasks_for_project
from aeris.data.task import get_task_by_uuid
from aeris.data.user import get_user_by_id
from aeris.decorators import decorate_project, decorate_task, decorate_user

query = QueryType()


@query.field("me")
async def resolve_me(_, info):
    user_id = info.context["user_id"]
    return decorate_user(await get_user_by_id(user_id))


@query.field("projects")
async def resolve_projects(_, info, pagination=None):
    user_id = info.context["user_id"]
    return [decorate_project(project) for project in await get_projects(user_id, pagination)]


@query.field("project")
async def resolve_project(_, info, id):
    user_id = info.context["user_id"]
    project = await get_project_by_uuid(id, user_id)

    if not project:
        return None

    return decorate_project(project)


@query.field("tasks")
async def resolve_tasks(_, info, projectId, pagination=None, filters=None):
    user_id = info.context["user_id"]
    tasks = [decorate_task(task) for task in await get_tasks_for_project(projectId, user_id, pagination, filters)]
    edges = [{"cursor": task["id"], "node": task} for task in tasks]
    return {"edges": edges, "pageInfo": {"hasNextPage": False, "hasPreviousPage": False}}


@query.field("task")
async def resolve_task(_, info, id):
    user_id = info.context["user_id"]
    return decorate_task(await get_task_by_uuid(id, user_id))
