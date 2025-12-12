from datetime import UTC, datetime
from uuid import UUID

from database.models import PrimaryAsset, UsageEventType, Version
from database.models_enums import PrimaryAssetKind, VersionStatus
from fastapi import APIRouter, HTTPException, Query
from hatchet_sdk import Hatchet
from pydantic import BaseModel
from shared.interfaces.hatchet_interfaces import InspectorInput
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

from app.api.auth import UserToken
from app.api.session import CurrentSession
from app.authorization.fastapi import enforce_asset_action
from app.schemas.codebase_schema import (
    CodebaseGenerationRequest,
    CodebaseGenerationResponse,
)

router = APIRouter()


class VersionResponse(BaseModel):
    id: UUID
    vcs_hash: str | None
    created_at: datetime


class CodebaseVersionsResponse(BaseModel):
    versions: list[VersionResponse]
    total_count: int
    limit: int
    offset: int


@router.get(
    "/{codebase_id}/versions",
    summary="Get available codebase versions",
)
def get_codebase_versions(
    session: CurrentSession,
    user: UserToken,
    codebase_id: UUID,
    limit: int = Query(default=10, gt=0),
    offset: int = Query(default=0, ge=0),
) -> CodebaseVersionsResponse:
    enforce_asset_action(
        db=session, user=user, asset_id=codebase_id, action_key="codebase.view_versions"
    )

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
            vcs_hash=version.vcs_hash,
            created_at=version.created_at,
        )
        for version in versions
    ]

    return CodebaseVersionsResponse(
        versions=response_data, total_count=total_count, limit=limit, offset=offset
    )


@router.post(
    "/generate",
    summary="Execute codebase generation",
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

    primary_asset_ids = {v.primary_asset_id for v in result}
    for primary_asset_id in primary_asset_ids:
        enforce_asset_action(
            db=session,
            user=user,
            asset_id=primary_asset_id,
            action_key="codebase.generate_tech_docs",
        )

    if len(result) != len(request.version_ids):
        # Only proceed if all versions are able to be processed
        raise HTTPException(
            status_code=404, detail="Versions not found for provided ids"
        )

    total_codebase_size_in_bytes = 0
    for version in result:
        metadata = (
            version.root_node.misc_metadata
        )  # TODO: is this loaded as a dict? Or string?
        total_codebase_size_in_bytes += metadata["analyzable_bytes"]
    usage_balance = UsageService(session).get_usage_balance(user.organization_id)
    if bytes_to_sloc(total_codebase_size_in_bytes) > usage_balance.balance:
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
        metadata = version.root_node.misc_metadata
        codebase_size_in_bytes = metadata["analyzable_bytes"]
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
                timestamp=datetime.now(tz=UTC),
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
        version.status = VersionStatus.GENERATING
        session.add(version)
        session.commit()

    hatchet = Hatchet()
    inspector_task = hatchet.stubs.task(
        name="inspector-workflow",
        input_validator=InspectorInput,
    )

    for version in result:
        inspector_task.run_no_wait(InspectorInput(version_id=str(version.id)))
    return CodebaseGenerationResponse(call_id="1234")
