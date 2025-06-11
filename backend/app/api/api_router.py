from fastapi import APIRouter

from app.api.routes.api import healthcheck

api_router = APIRouter()


api_router.include_router(
    healthcheck.router, prefix="/healthcheck", tags=["healthcheck"]
)
