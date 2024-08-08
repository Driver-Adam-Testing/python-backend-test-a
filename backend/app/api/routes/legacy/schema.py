import strawberry
from fastapi import Depends
from strawberry.fastapi import BaseContext, GraphQLRouter
from strawberry.schema.config import StrawberryConfig

from app.api.auth import get_current_m2m, get_current_user
from app.api.routes.legacy.scalars import JSON
from app.api.session import get_db

from .logging_extension import LoggingExtension
from .mutations import Mutation
from .queries import Query

schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    config=StrawberryConfig(auto_camel_case=False),
    scalar_overrides={dict: JSON},  # type: ignore
    extensions=[LoggingExtension],
)


class Context(BaseContext):
    def __init__(self, session, user, m2m):
        self.session = session
        self.user = user
        self.m2m = m2m
        super().__init__()


async def get_context(
    user=Depends(get_current_user),
    m2m=Depends(get_current_m2m),
    session=Depends(get_db),
) -> Context:
    context = Context(session, user, m2m)
    return context


graphql_router: GraphQLRouter = GraphQLRouter(schema, context_getter=get_context)

sandbox_router: GraphQLRouter = GraphQLRouter(
    schema,
    path="/apollo-sandbox/",
    graphql_ide="apollo-sandbox",
    context_getter=get_context,
)
