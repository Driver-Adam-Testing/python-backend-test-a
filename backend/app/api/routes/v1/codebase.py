from datetime import datetime
from uuid import UUID

import modal
from database.models_v1 import UsageEventType
from database.models_v2 import PrimaryAsset, Version
from database.models_v2_enums import PrimaryAssetKind, VersionStatus
from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from shared.interfaces.usage.event_metadata import (
    UsageEventMetadata,
    UsageMetric,
    UsageSessionMetadata,
)
from shared.usage.llm_session import LLMUsageSession
from shared.usage.usage_service import UsageService
from shared.usage.utils import bytes_to_sloc
from sqlalchemy.orm import selectinload
from sqlmodel import func, select

from app.api.auth import ContentEditorPermission, ContentReadonlyPermission, UserToken
from app.api.session import CurrentSession
from app.schemas.codebase_schema import (
    CodebaseAnalysisRequest,
    CodebaseAnalysisResponse,
    CodebaseAnalysisResult,
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
        .options(
            selectinload(Version.root_node),
            selectinload(Version.primary_asset),
        )
    )
    result = session.exec(query).all()
    if len(result) != len(request.version_ids):
        # Only proceed if all versions are able to be processed
        raise HTTPException(
            status_code=404, detail="Versions not found for provided ids"
        )

    codebase_size_in_bytes = 0
    for version in result:
        metadata = (
            version.root_node.misc_metadata
        )  # TODO: is this loaded as a dict? Or string?
        codebase_size_in_bytes += metadata["analyzable_bytes"]
    usage_balance = UsageService(session).get_usage_balance(user.organization_id)
    if bytes_to_sloc(codebase_size_in_bytes) > usage_balance.balance:
        raise HTTPException(
            status_code=402,
            detail="Not enough usage balance",
        )

    for version in result:
        session_meta = UsageSessionMetadata(
            content_type="codebase",
            content_id=str(version.primary_asset_id),
            content_name=version.primary_asset.display_name,
            version_id=str(version.id),
        )
        with LLMUsageSession(
            user.organization_id, user.user_id, session_meta
        ) as llm_session:
            usage_metric = UsageMetric(
                session_id=llm_session.session_id,
                organization_id=user.organization_id,
                user_id=user.user_id,
                event_source="codebase_onboarding",  # TODO make enum
                bytes_in=-codebase_size_in_bytes,
                bytes_out=0,
                tokens_in=0,
                tokens_out=0,
                timestamp=datetime.now(tz=datetime.UTC),
                event_type=UsageEventType.ONBOARDING_USAGE_DEBIT,
                event_metadata=UsageEventMetadata(
                    model="None",
                    provider="None",
                    input={},
                    output="",
                    sloc=bytes_to_sloc(codebase_size_in_bytes),
                ),
            )
            llm_session.commit_event_now(usage_metric)

    inspect_db = modal.Function.lookup("inspector-v2", "inspect_db")
    for version in result:
        inspect_db.spawn(version.id)
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
