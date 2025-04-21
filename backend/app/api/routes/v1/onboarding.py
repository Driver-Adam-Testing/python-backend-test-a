import uuid

import modal
from database.models_v2 import Version
from database.models_v2_enums import PrimaryAssetKind, VersionStatus
from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy.orm.exc import NoResultFound

from app.api.auth import M2MToken
from app.api.session import CurrentSession
from app.core.config import settings

router = APIRouter()


class AssetConnection(BaseModel):
    # TODO: Is the status being consumed somewhere? Otherwise this isn't appropriate.
    status: str = "OK"
    call_id: str | None = None


class AssetConnectionRequest(BaseModel):
    org_id: str
    download_url: str | None
    asset_name: str
    asset_kind: PrimaryAssetKind
    version_id: uuid.UUID
    provider: str  # TODO: provider should be an enum
    should_process: bool


@router.post(
    "/",
    summary="Trigger Asset Connection",
    response_description="Return HTTP Status Code 200 (OK)",
)
def trigger_asset_connection(
    current_token: M2MToken,
    session: CurrentSession,
    trigger_body: AssetConnectionRequest,
) -> AssetConnection:
    if not trigger_body.should_process:
        with session.begin():
            try:
                version = session.get_one(Version, trigger_body.version_id)
            except NoResultFound as e:
                raise Exception(
                    f"Version {trigger_body.version_id} not found. May have been deleted by user before execution. Version was flagged by GuardDuty as well."
                ) from e
            version.status = VersionStatus.CONNECTION_FAILED
            session.add(version)
        raise Exception(
            f"GuardDuty found something. Version {trigger_body.version_id} set to CONNECTION_FAILED."
        )

    if trigger_body.asset_kind == PrimaryAssetKind.CODEBASE:
        run_codebase_connection = modal.Function.lookup(
            "inspector-v2", "run_codebase_connection"
        )

        call = run_codebase_connection.spawn(
            presigned_url=trigger_body.download_url,
            provisional_codebase_name=trigger_body.asset_name,
            org_id=trigger_body.org_id,
            version_id=trigger_body.version_id,
            provider=trigger_body.provider,
        )
    elif trigger_body.asset_kind == PrimaryAssetKind.FILE:
        create_and_embed_pdf_summaries = modal.Function.lookup(
            app_name="pdf-summary-embedding",
            # TODO: this line is not need once we deploy to production.
            environment_name=settings.MODAL_ENVIRONMENT,
            tag="create_and_embed_pdf_summaries",
        )
        call = create_and_embed_pdf_summaries.spawn(
            trigger_body.download_url,
            trigger_body.version_id,
            trigger_body.asset_name,
            trigger_body.org_id,
        )

    return AssetConnection(status="OK", call_id=call.object_id)


# class PdfOnboardingRequestBody(BaseModel):
#     node_id: str | None = None
#
#
# @router.post(
#     "/generate-pdf-summaries",
#     summary="Trigger PDF Summarization and Embedding",
#     response_description="Return HTTP Status Code 200 (OK)",
# )
# def trigger_pdf_summary_processing(
#     current_token: M2MToken, session: CurrentSession, body: PdfOnboardingRequestBody
# ) -> AssetConnection:
#     logging.info("Triggering pdf summary creation...")
#     # archive_name = Path(trigger_body.object_key).name
#     create_and_embed_pdf_summaries = modal.Function.lookup(
#         app_name="pdf-summary-embedding",
#         # TODO: this line is not need once we deploy to production.
#         environment_name=settings.MODAL_ENVIRONMENT,
#         tag="create_and_embed_pdf_summaries",
#     )
#     call = create_and_embed_pdf_summaries.spawn(body.node_id)
#
#     return AssetConnection(status="OK", call_id=call.object_id)
