from fastapi import APIRouter

from app.api.routes.api import search

api_router = APIRouter()


api_router.include_router(search.router, prefix="/search", tags=["api_search"])
