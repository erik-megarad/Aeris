from ariadne import MutationType

from aeris.data.project import create_project, delete_project, update_project
from aeris.data.task import create_task, create_task_embedding, delete_task, update_task
from aeris.decorators import decorate_project, decorate_task
from aeris.embeddings import generate_openai_embedding

mutation = MutationType()


# Projects
@mutation.field("createProject")
async def resolve_create_project(_, info, name, description=None):
    user_id = info.context["user_id"]
    return decorate_project(await create_project(user_id, name, description))


@mutation.field("updateProject")
async def resolve_update_project(_, info, id, name=None, description=None):
    user_id = info.context["user_id"]
    return decorate_project(await update_project(id, user_id, name, description))


@mutation.field("deleteProject")
async def resolve_delete_project(_, info, id):
    user_id = info.context["user_id"]
    return decorate_project(await delete_project(id, user_id))


# Tasks
@mutation.field("createTask")
async def resolve_create_task(_, info, projectId, name, input):
    user_id = info.context["user_id"]
    task = await create_task(projectId, user_id, name, input)
    if not task:
        # TODO: Error handling
        return None

    embedding = generate_openai_embedding(input)
    await create_task_embedding(task["id"], embedding)

    return decorate_task(task)


@mutation.field("updateTask")
async def resolve_update_task(_, info, id, name=None, input=None, state=None, result=None):
    user_id = info.context["user_id"]
    return decorate_task(await update_task(id, user_id, name, input, state, result))


@mutation.field("deleteTask")
async def resolve_delete_task(_, info, id):
    user_id = info.context["user_id"]
    return decorate_task(await delete_task(id, user_id))
