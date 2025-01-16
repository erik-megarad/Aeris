from ariadne import load_schema_from_path, make_executable_schema
from ariadne.asgi import GraphQL
from ariadne.asgi.handlers import GraphQLHTTPHandler
from fastapi.responses import JSONResponse
from graphql import GraphQLError
from starlette.requests import Request
from starlette.responses import Response

from aeris.api_key import verify_api_key
from aeris.resolvers.mutations import mutation
from aeris.resolvers.queries import query
from aeris.resolvers.types import event, project, task, user

type_defs = load_schema_from_path("aeris/schemas/schema.graphql")


class AuthenticationError(GraphQLError):
    def __init__(self, message: str) -> None:
        self.status_code = 401
        super().__init__(message, extensions={"code": "UNAUTHENTICATED"})


# Custom error formatter
def custom_error_formatter(error, debug=False):
    # Check if it's an UnauthorizedError
    if isinstance(error.original_error, AuthenticationError):
        return {
            "message": error.original_error.message,
            "extensions": {
                "code": "UNAUTHORIZED",
                "status_code": error.original_error.status_code,
            },
        }

    # Default behavior for other errors
    return {
        "message": str(error),
        "extensions": {"code": "INTERNAL_SERVER_ERROR"},
    }


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
        raise AuthenticationError(f"Authentication failed: {e}") from e

    return {
        "request": request,
        "project_id": verification["project_id"],
        "user_id": verification["user_id"],
    }


class CustomGraphQL(GraphQL):
    async def process_result(self, request, result):
        # Check for custom status codes in errors
        status_code = 200  # Default
        if "errors" in result:
            for error in result["errors"]:
                if "extensions" in error and "status_code" in error["extensions"]:
                    status_code = error["extensions"]["status_code"]
                    break

        # Return response with appropriate status code
        return JSONResponse(result, status_code=status_code)


class ContextErrorHandler(GraphQLHTTPHandler):
    async def graphql_http_server(self, request: Request) -> Response:
        try:
            return await super().graphql_http_server(request)

        except AuthenticationError as e:
            return JSONResponse(
                {
                    "errors": [
                        {"message": e.message, "extensions": {"code": "UNAUTHORIZED", "status_code": e.status_code}}
                    ]
                },
                status_code=e.status_code,
            )


schema = make_executable_schema(type_defs, query, mutation, project, task, event, user)


# ASGI app
app = CustomGraphQL(
    schema, error_formatter=custom_error_formatter, context_value=get_context_value, http_handler=ContextErrorHandler()
)
