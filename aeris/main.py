from ariadne import load_schema_from_path, make_executable_schema
from ariadne.asgi import GraphQL
from starlette.requests import Request

from aeris.api_key import verify_api_key
from aeris.resolvers.mutations import mutation
from aeris.resolvers.queries import query
from aeris.resolvers.types import event, project, task, user

type_defs = load_schema_from_path("aeris/schemas/schema.graphql")


async def get_context_value(request: Request, _):
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        api_key = auth_header[len("Bearer ") :].strip()
    else:
        api_key = None

    if not api_key:
        raise ValueError("Missing API key")

    try:
        verification = await verify_api_key(api_key)
    except ValueError as e:
        raise ValueError(f"Authentication failed: {e}") from e

    return {
        "request": request,
        "project_id": verification["project_id"],
        "user_id": verification["user_id"],
    }


schema = make_executable_schema(type_defs, query, mutation, project, task, event, user)


# ASGI app
app = GraphQL(
    schema,
    context_value=get_context_value,
)
