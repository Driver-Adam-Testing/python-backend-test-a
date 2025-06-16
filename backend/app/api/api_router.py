from fastapi import APIRouter

from app.api.routes.api import healthcheck, search

api_router = APIRouter()


api_router.include_router(
    healthcheck.router, prefix="/healthcheck", tags=["healthcheck"]
)

api_router.include_router(search.router, prefix="/search", tags=["api_search"])
