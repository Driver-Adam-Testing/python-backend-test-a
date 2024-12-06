from datetime import datetime
from uuid import UUID

from database.models_v1 import (
    DerivedContent,
    DerivedContentType,
    InspectionVersion,
    Workspace,
)
from fastapi import APIRouter, Query
from pydantic import BaseModel
from sqlmodel import func, select

from app.api.auth import ContentReadonlyPermission, UserToken
from app.api.session import CurrentSession
from app.schemas.codebase_schema import (
    CodebaseAnalysisRequest,
    CodebaseAnalysisResponse,
    CodebaseAnalysisResult,
)
from app.services.codebase_service import CodebaseService

router = APIRouter()


class VersionResponse(BaseModel):
    id: UUID
    version: str
    display_name: str | None
    created_at: datetime


class CodebaseVersionsResponse(BaseModel):
    versions: list[VersionResponse]
    total_count: int
    limit: int
    offset: int


@router.get(
    "/{codebase_id}/versions",
    summary="Get available codebase versions",
    dependencies=[ContentReadonlyPermission],
)
def get_codebase_versions(
    session: CurrentSession,
    user: UserToken,
    codebase_id: UUID,
    limit: int = Query(default=10, gt=0),
    offset: int = Query(default=0, ge=0),
) -> CodebaseVersionsResponse:
    codebase_type = session.exec(
        select(DerivedContentType).where(DerivedContentType.type_name == "codebase")
    ).first()
    codebase_type_id = codebase_type.id
    statement = (
        select(InspectionVersion)
        .join(DerivedContent)
        .join(Workspace)
        .where(
            DerivedContent.codebase_id == codebase_id,
            Workspace.organization_id == user.organization_id,
            DerivedContent.content_type_id == codebase_type_id,
            InspectionVersion.version.isnot(None),
        )
        .order_by(InspectionVersion.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    versions = session.exec(statement).all()

    total_count = session.exec(
        select(func.count(InspectionVersion.id))
        .join(DerivedContent)
        .join(Workspace)
        .where(
            DerivedContent.codebase_id == codebase_id,
            Workspace.organization_id == user.organization_id,
            DerivedContent.content_type_id == codebase_type_id,
            InspectionVersion.version.isnot(None),
        )
    ).one()

    response_data = [
        VersionResponse(
            id=version.id,
            version=version.version,
            display_name=version.display_name,
            created_at=version.created_at,
        )
        for version in versions
    ]

    return CodebaseVersionsResponse(
        versions=response_data, total_count=total_count, limit=limit, offset=offset
    )


@router.post("/analysis", summary="Execute codebase analysis")
def exec_codebase_analysis(
    session: CurrentSession, user: UserToken, request: CodebaseAnalysisRequest
) -> CodebaseAnalysisResponse:
    return CodebaseService.execute_codebase_analysis(request)


@router.get("/analysis/{call_id}", summary="Get codebase analysis results")
def get_codebase_analysis(
    session: CurrentSession, user: UserToken, call_id: str
) -> CodebaseAnalysisResult:
    return CodebaseService.get_codebase_analysis_results(call_id)
