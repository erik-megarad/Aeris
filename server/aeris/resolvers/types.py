import json

from ariadne import ObjectType, ScalarType

from aeris.data.project import get_tasks_for_project
from aeris.data.task import get_embeddings_for_task, get_metadata_for_task, get_task_by_uuid

project = ObjectType("Project")
task = ObjectType("Task")
event = ObjectType("Event")
user = ObjectType("User")


# Resolve related fields
@project.field("tasks")
def resolve_project_tasks(obj, info, pagination=None, filters=None):
    return get_tasks_for_project(obj.id, pagination, filters)


@task.field("embeddings")
async def resolve_task_embeddings(obj, info):
    user_id = info.context["user_id"]
    task_record = await get_task_by_uuid(obj["id"], user_id)
    result = await get_embeddings_for_task(task_record["id"])
    decorated = [
        {"id": embedding["id"], "task_id": task_record["id"], "embedding": embedding["embedding"].tolist()}
        for embedding in result
    ]
    return decorated


@task.field("metadata")
async def resolve_task_metadata(obj, info):
    user_id = info.context["user_id"]
    task_record = await get_task_by_uuid(obj["id"], user_id)
    return await get_metadata_for_task(task_record["id"])


# Define the JSON scalar
json_scalar = ScalarType("JSON")


@json_scalar.serializer
def serialize_json(value):
    return value


@json_scalar.value_parser
def parse_json_value(value):
    return value


@json_scalar.literal_parser
def parse_json_literal(ast, _variables=None):
    try:
        return json.loads(ast.value)
    except (ValueError, TypeError):
        return None
