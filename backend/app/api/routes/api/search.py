import uuid

from app.api.auth import ApiKeyToken
from app.api.session import CurrentSession
from fastapi import APIRouter
from pydantic import BaseModel
from shared.v3.app.static.tools.hybrid_search import HybridSearchTool
from shared.v3.utils.datasource import DataSource
from shared.v3.utils.references import Reference

router = APIRouter()


class SearchRequest(BaseModel):
    query: str
    node_ids: list[uuid.UUID] | None = None
    relative_paths: list[str] | None = None


@router.post("/")
async def search(
    user: ApiKeyToken, session: CurrentSession, payload: SearchRequest
) -> list[Reference]:
    search_tool = HybridSearchTool(
        search_query=payload.query,
    )
    if payload.node_ids:
        datasource = DataSource.from_node_ids(
            organization_id=user.organization_id,
            node_ids=payload.node_ids,
        )
    elif payload.relative_paths:
        datasource = DataSource.from_relative_paths(
            organization_id=user.organization_id,
            relative_paths=payload.relative_paths,
        )
    else:
        raise ValueError("Either node_ids or relative_paths must be provided")
    search_tool.execute(
        tool_call_id="",
        datasource=datasource,
    )
    return search_tool._references
