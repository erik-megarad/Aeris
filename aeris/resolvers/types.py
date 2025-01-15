import json

from ariadne import ObjectType, ScalarType

project = ObjectType("Project")
task = ObjectType("Task")
event = ObjectType("Event")
user = ObjectType("User")


# Resolve related fields
@project.field("tasks")
def resolve_project_tasks(obj, info, pagination=None, filters=None):
    return get_tasks_for_project(obj.id, pagination, filters)


@task.field("embeddings")
def resolve_task_embeddings(obj, info):
    return get_embeddings_for_task(obj.id)


@task.field("metadata")
def resolve_task_metadata(obj, info):
    return get_metadata_for_task(obj.id)


@event.field("eventData")
def resolve_event_data(obj, info):
    return obj.event_data  # Assuming it's stored as JSON in the database


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
