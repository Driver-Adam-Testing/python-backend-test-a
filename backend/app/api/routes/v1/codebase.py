from datetime import datetime
from uuid import UUID

from database.models_v2 import PrimaryAsset, Version
from database.models_v2_enums import PrimaryAssetKind, VersionStatus
from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from shared.usage.usage_service import UsageService
from sqlmodel import func, select

from app.api.auth import ContentEditorPermission, ContentReadonlyPermission, UserToken
from app.api.session import CurrentSession
from app.schemas.codebase_schema import (
    CodebaseAnalysisRequest,
    CodebaseAnalysisResponse,
    CodebaseAnalysisResult,
    CodebaseConnectionRequest,
    CodebaseConnectionResponse,
    CodebaseGenerationRequest,
    CodebaseGenerationResponse,
    CodebaseOnboardRequest,
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
    # Find the primary asset that represents the codebase
    primary_asset_id = codebase_id  # URL MISNOMER
    primary_asset = session.exec(
        select(PrimaryAsset).where(
            PrimaryAsset.id == primary_asset_id,
            PrimaryAsset.organization_id == user.organization_id,
            PrimaryAsset.kind == PrimaryAssetKind.CODEBASE,
        )
    ).one_or_none()

    if not primary_asset:
        # If not found, raise an error
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Codebase not found")

    # Query versions associated with this primary asset
    statement = (
        select(Version)
        .where(Version.primary_asset_id == primary_asset.id)
        .order_by(Version.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    versions = session.exec(statement).all()

    # Count total number of versions for pagination
    total_count = session.exec(
        select(func.count(Version.id)).where(
            Version.primary_asset_id == primary_asset.id
        )
    ).one()

    response_data = [
        VersionResponse(
            id=version.id,
            # Here we treat the version's display_name as the "version" string
            version=version.display_name,
            display_name=version.display_name,
            created_at=version.created_at if version.created_at else datetime.now(),
        )
        for version in versions
    ]

    return CodebaseVersionsResponse(
        versions=response_data, total_count=total_count, limit=limit, offset=offset
    )


@router.post(
    "/analysis",
    summary="Execute codebase analysis",
    dependencies=[ContentEditorPermission],
)
def exec_codebase_analysis(
    user: UserToken,
    request: CodebaseAnalysisRequest,
) -> CodebaseAnalysisResponse:
    return CodebaseService.execute_codebase_analysis(
        user.organization_id, request.download_url
    )


@router.post(
    "/connect",
    summary="Execute codebase connection",
    dependencies=[ContentEditorPermission],
)
def exec_codebase_connection(
    user: UserToken,
    request: CodebaseConnectionRequest,
) -> CodebaseConnectionResponse:
    return CodebaseService.execute_codebase_connection(
        user.organization_id, request.download_urls
    )


@router.post(
    "/generate",
    summary="Execute codebase generation",
    dependencies=[ContentEditorPermission],
)
def exec_codebase_generation(
    session: CurrentSession,
    user: UserToken,
    request: CodebaseGenerationRequest,
) -> CodebaseGenerationResponse:
    query = (
        select(Version)
        .join(PrimaryAsset)
        .where(
            Version.id.in_(request.version_ids),
            Version.status == VersionStatus.CONNECTED,
            PrimaryAsset.organization_id == user.organization_id,
        )
    )
    result = session.exec(query).all()
    if len(result) != len(request.version_ids):
        raise HTTPException(
            status_code=404, detail="Versions not found for provided ids"
        )

    # TODO: check usage before generation
    # TODO call execute function or modal function for each, or create new modal function that handles delegation
    return CodebaseGenerationResponse(call_id="1234")


@router.get(
    "/analysis/{call_id}",
    summary="Get codebase analysis results",
    dependencies=[ContentEditorPermission],
)
def get_codebase_analysis(
    call_id: str,
) -> CodebaseAnalysisResult:
    analysis_response = CodebaseService.get_codebase_analysis_results(call_id)
    if analysis_response.status in ["error", "expired"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Bad Request"
        )

    return analysis_response


@router.post(
    "/onboard",
    summary="Trigger codebase onboarding",
    dependencies=[ContentEditorPermission],
)
def trigger_codebase_onboarding(
    session: CurrentSession,
    user: UserToken,
    request: CodebaseOnboardRequest,
) -> JSONResponse:
    analysis = CodebaseService.get_codebase_analysis_results(request.call_id)

    if analysis.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Bad Request"
        )

    analyzable_sloc = analysis.result.analyzable_sloc

    available_usage = UsageService(session).get_usage_balance(user.organization_id)

    if analyzable_sloc > available_usage.balance:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Bad Request"
        )

    CodebaseService.trigger_codebase_onboarding(
        user.organization_id, request.codebase_object_key
    )
    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED, content={"message": "Accepted"}
    )
