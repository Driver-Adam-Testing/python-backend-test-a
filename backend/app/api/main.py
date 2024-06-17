from fastapi import APIRouter

from app.core.config import settings
from app.api.routes.legacy.schema import graphql_router, sandbox_router
from app.api.routes.v1 import workspace, healthcheck

api_router = APIRouter()

api_router.include_router(graphql_router, prefix="/graphql", tags=["legacy-graphql"])
api_router.include_router(workspace.router, prefix="/workspace", tags=["workspace"])
api_router.include_router(healthcheck.router, prefix="/healthcheck", tags=["healthcheck"])
if(settings.ENVIRONMENT != "production"):
    api_router.include_router(sandbox_router, prefix="/sandbox", tags=["legacy-sandbox"])
