from fastapi import APIRouter

from app.api.routes import utils
from app.api.routes.v1 import workspace

api_router = APIRouter()
api_router.include_router(utils.router, prefix="/utils", tags=["utils"])
# api_router.include_router(items.router, prefix="/items", tags=["items"])
api_router.include_router(workspace.router, prefix="/workspace", tags=["workspace"])
# api_router.include_router(codebase.router, prefix="/codebase", tags=["codebase"])
