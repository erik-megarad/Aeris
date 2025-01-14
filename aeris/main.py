from ariadne import QueryType, make_executable_schema
from ariadne.asgi import GraphQL
from fastapi import FastAPI

# Define GraphQL schema
type_defs = """
type Query {
    hello: String!
}
"""

query = QueryType()

@query.field("hello")
def resolve_hello(_, info):
    return "Welcome to Aeris!"

schema = make_executable_schema(type_defs, query)

app = FastAPI()

app.add_route("/graphql", GraphQL(schema))

