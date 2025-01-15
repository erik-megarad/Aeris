from ariadne import MutationType

mutation = MutationType()


# Example Project Mutations
@mutation.field("createProject")
def resolve_create_project(_, info, name, description=None):
    user_id = info.context["user_id"]
    return create_project(user_id, name, description)


@mutation.field("updateProject")
def resolve_update_project(_, info, id, name=None, description=None):
    return update_project(id, name, description)


@mutation.field("deleteProject")
def resolve_delete_project(_, info, id):
    return delete_project(id)


# Example Task Mutations
@mutation.field("createTask")
def resolve_create_task(_, info, projectId, name, input):
    return create_task(projectId, name, input)


@mutation.field("updateTask")
def resolve_update_task(_, info, id, name=None, input=None, state=None, result=None):
    return update_task(id, name, input, state, result)


@mutation.field("deleteTask")
def resolve_delete_task(_, info, id):
    return delete_task(id)
