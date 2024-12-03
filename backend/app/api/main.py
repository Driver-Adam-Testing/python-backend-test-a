from fastapi import APIRouter

from app.api.routes.legacy.schema import graphql_router, sandbox_router
from app.api.routes.v1 import (
    agent_pipelines,
    codebase,
    content,
    git_provider,
    healthcheck,
    instructions,
    onboarding,
    organization,
    search,
    tags,
    upload,
    usage,
    user,
)
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
api_router.include_router(content.router, prefix="/content", tags=["content"])
api_router.include_router(codebase.router, prefix="/codebases", tags=["codebase"])
api_router.include_router(tags.router, prefix="/tags", tags=["tags"])
api_router.include_router(
    instructions.router, prefix="/instructions", tags=["instructions"]
)
api_router.include_router(upload.router, prefix="/upload", tags=["upload"])
api_router.include_router(
    agent_pipelines.router, prefix="/agent_pipelines", tags=["agent_pipelines"]
)
api_router.include_router(usage.router, prefix="/usage", tags=["usage"])
api_router.include_router(user.router, prefix="/user", tags=["user"])
api_router.include_router(
    organization.router, prefix="/organization", tags=["organization"]
)

if settings.ENVIRONMENT != "production":
    api_router.include_router(
        sandbox_router, prefix="/sandbox", tags=["legacy-sandbox"]
    )
