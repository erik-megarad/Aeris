from ariadne import QueryType

from aeris.data.user import get_user_by_id

query = QueryType()


# Example User resolver
@query.field("me")
async def resolve_me(_, info):
    user_id = info.context["user_id"]
    user = await get_user_by_id(user_id)
    return dict(user)


# Projects resolver
@query.field("projects")
def resolve_projects(_, info, pagination=None):
    user_id = info.context["user_id"]
    return get_projects_for_user(user_id, pagination)


# Single Project resolver
@query.field("project")
def resolve_project(_, info, id):
    return get_project_by_id(id)


# Tasks resolver
@query.field("tasks")
def resolve_tasks(_, info, projectId, pagination=None, filters=None):
    return get_tasks_for_project(projectId, pagination, filters)


# Single Task resolver
@query.field("task")
def resolve_task(_, info, id):
    return get_task_by_id(id)
