from fastapi import APIRouter

from app.api.routes.legacy.schema import graphql_router, sandbox_router

from app.api.routes.v1 import git_provider, healthcheck, onboarding, search, instructions

from app.core.config import settings

api_router = APIRouter()

api_router.include_router(graphql_router, prefix="/graphql", tags=["legacy-graphql"])
api_router.include_router(
    healthcheck.router, prefix="/healthcheck", tags=["healthcheck"]
)
api_router.include_router(
    git_provider.router, prefix="/git-provider", tags=["git-provider"]
)
api_router.include_router(onboarding.router, prefix="/onboarding", tags=["onboarding"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(instructions.router, prefix="/instructions", tags=["instructions"])
if settings.ENVIRONMENT != "production":
    api_router.include_router(
        sandbox_router, prefix="/sandbox", tags=["legacy-sandbox"]
    )
