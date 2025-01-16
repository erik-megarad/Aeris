from ariadne import MutationType

from aeris.data.project import create_project, delete_project, update_project
from aeris.data.task import create_task, delete_task, update_task

mutation = MutationType()


# Example Project Mutations
@mutation.field("createProject")
def resolve_create_project(_, info, name, description=None):
    user_id = info.context["user_id"]
    return create_project(user_id, name, description)


@mutation.field("updateProject")
def resolve_update_project(_, info, id, name=None, description=None):
    user_id = info.context["user_id"]
    return update_project(id, user_id, name, description)


@mutation.field("deleteProject")
def resolve_delete_project(_, info, id):
    user_id = info.context["user_id"]
    return delete_project(id, user_id)


# Example Task Mutations
@mutation.field("createTask")
def resolve_create_task(_, info, projectId, name, input):
    user_id = info.context["user_id"]
    return create_task(projectId, user_id, name, input)


@mutation.field("updateTask")
def resolve_update_task(_, info, id, name=None, input=None, state=None, result=None):
    user_id = info.context["user_id"]
    return update_task(id, user_id, name, input, state, result)


@mutation.field("deleteTask")
def resolve_delete_task(_, info, id):
    user_id = info.context["user_id"]
    return delete_task(id, user_id)
