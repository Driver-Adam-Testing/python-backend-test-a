from fastapi import APIRouter

from app.api.routes.api import migrated_studio_endpoints, search

api_router = APIRouter()


api_router.include_router(search.router, prefix="/search", tags=["api_search"])

api_router.include_router(
    migrated_studio_endpoints.router,
    prefix="/tmp",
    tags=["migrated_studio_endpoints"],
)
