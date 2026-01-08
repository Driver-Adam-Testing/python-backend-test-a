import uuid

from database.models import Version
from database.models_enums import PrimaryAssetKind, VersionStatus
from fastapi import APIRouter
from hatchet_sdk import Hatchet
from pydantic import BaseModel
from shared.interfaces.hatchet_interfaces import (
    PDFProcessingInput,
    RunCodebaseConnectionInput,
)
from sqlalchemy.orm.exc import NoResultFound

from app.api.auth import M2MToken
from app.api.session import CurrentSession

router = APIRouter()


class AssetConnection(BaseModel):
    # TODO: Is the status being consumed somewhere? Otherwise this isn't appropriate.
    status: str = "OK"
    call_id: str | None = None


class AssetConnectionRequestParams(BaseModel):
    org_id: str
    asset_name: str
    asset_kind: PrimaryAssetKind
    provider: str  # TODO: provider should be an enum
    download_url: str


class AssetConnectionRequest(BaseModel):
    version_id: uuid.UUID
    should_process: bool
    params: AssetConnectionRequestParams | None


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

    hatchet = Hatchet()
    match trigger_body.params.asset_kind:
        case PrimaryAssetKind.CODEBASE:
            run_codebase_connection_task = hatchet.stubs.task(
                name="run-codebase-connection-workflow",
                input_validator=RunCodebaseConnectionInput,
            )
            call = run_codebase_connection_task.run_no_wait(
                RunCodebaseConnectionInput(
                    presigned_url=trigger_body.params.download_url,
                    provisional_codebase_name=trigger_body.params.asset_name,
                    org_id=trigger_body.params.org_id,
                    version_id=str(trigger_body.version_id),
                    provider=trigger_body.params.provider,
                )
            )

        case PrimaryAssetKind.FILE:
            pdf_processing_task = hatchet.stubs.task(
                name="pdf-processing-workflow",
                input_validator=PDFProcessingInput,
            )
            call = pdf_processing_task.run_no_wait(
                PDFProcessingInput(
                    presigned_url=trigger_body.params.download_url,
                    version_id=str(trigger_body.version_id),
                    asset_name=trigger_body.params.asset_name,
                    org_id=trigger_body.params.org_id,
                )
            )
        case _:
            raise Exception(
                f"Asset kind {trigger_body.params.asset_kind} not supported for connection."
            )

    return AssetConnection(status="OK", call_id=str(call.workflow_run_id))
