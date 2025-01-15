from ariadne import QueryType

query = QueryType()


# Example User resolver
@query.field("me")
def resolve_me(_, info):
    import pdb

    pdb.set_trace()
    user_id = info.context["user_id"]  # Example: Authenticated user ID from context
    return get_user_by_id(user_id)  # Implement `get_user_by_id` in your data access layer


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
