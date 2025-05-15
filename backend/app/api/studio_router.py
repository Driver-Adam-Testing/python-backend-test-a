from fastapi import APIRouter

from app.api.routes.legacy.schema import graphql_router, sandbox_router
from app.api.routes.v1 import (
    agent_pipelines,
    codebase,
    content,
    git_provider,
    healthcheck,
    onboarding,
    organization,
    search,
    subscription,
    tags,
    upload,
    usage,
    user,
)

# ruff: noqa: F401
from app.api.routes.v2 import (
    autodocs,
    chat,
    contents,
    convenience_endpoints,
    document_sources,
    generate,
    nodes,
    primary_asset_tags,
    primary_assets,
    versions,
)
from app.api.routes.v2 import (
    router as v2_router,
)
from app.api.routes.v2 import (
    tags as v2_tags,
)
from app.core.config import settings

studio_router = APIRouter()

studio_router.include_router(graphql_router, prefix="/graphql", tags=["legacy-graphql"])
studio_router.include_router(
    healthcheck.router, prefix="/healthcheck", tags=["healthcheck"]
)
studio_router.include_router(
    git_provider.router, prefix="/git-provider", tags=["git-provider"]
)
studio_router.include_router(
    onboarding.router, prefix="/onboarding", tags=["onboarding"]
)
studio_router.include_router(search.router, prefix="/search", tags=["search"])
studio_router.include_router(content.router, prefix="/content", tags=["content"])
studio_router.include_router(codebase.router, prefix="/codebases", tags=["codebase"])
studio_router.include_router(tags.router, prefix="/tags", tags=["tags"])
studio_router.include_router(upload.router, prefix="/upload", tags=["upload"])
studio_router.include_router(
    agent_pipelines.router, prefix="/agent_pipelines", tags=["agent_pipelines"]
)
studio_router.include_router(usage.router, prefix="/usage", tags=["usage"])
studio_router.include_router(user.router, prefix="/user", tags=["user"])
studio_router.include_router(
    organization.router, prefix="/organization", tags=["organization"]
)
studio_router.include_router(v2_router.router, prefix="/node", tags=["node"])

if settings.ENVIRONMENT != "production":
    studio_router.include_router(
        sandbox_router, prefix="/sandbox", tags=["legacy-sandbox"]
    )

studio_router.include_router(
    subscription.router, prefix="/subscription", tags=["subscription"]
)

studio_router.include_router(generate.router, prefix="/generate", tags=["generate"])
studio_router.include_router(chat.router, prefix="/chat", tags=["chat"])
studio_router.include_router(autodocs.router, prefix="/autodocs", tags=["autodocs"])
