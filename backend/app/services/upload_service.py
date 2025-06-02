import hashlib
import os
import re
from urllib.parse import unquote_plus

from database.models_v2 import (
    PrimaryAsset,
    Version,
)
from database.models_v2_enums import (
    PrimaryAssetKind,
    VersionStatus,
)
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from app.api.auth import UserToken
from app.api.session import CurrentSession
from app.core.logger import logger
from app.schemas.upload_schema import (
    UploadAutoDocConfigRequest,
    UploadAutoDocConfigResponse,
    UploadRequest,
    UploadResponse,
)
from app.utils.aws_s3 import (
    generate_put_presigned_url,
)


class UploadService:
    def __init__(self, session: CurrentSession) -> None:
        self.session = session

    def create_asset_version_and_upload_url(
        self, user: UserToken, request: UploadRequest
    ) -> UploadResponse:
        file_name = os.path.basename(request.file_path)
        if file_name.lower().endswith(".zip"):
            asset_name = os.path.splitext(file_name)[0]
            asset_kind = PrimaryAssetKind.CODEBASE
            content_type = "application/zip"
            codebase_settings_auto_commit_docs = False
        elif file_name.lower().endswith(".pdf"):
            asset_name = file_name
            asset_kind = PrimaryAssetKind.FILE
            content_type = "application/pdf"
            codebase_settings_auto_commit_docs = None
        else:
            raise HTTPException(
                status_code=400, detail="File must be a zip or pdf file"
            )

        file_name = re.sub(r"[^a-zA-Z0-9.]", "_", file_name)
        file_name = file_name.replace(" ", "_")

        org_id = user.organization_id
        org_id_hash = hashlib.sha256(org_id.encode()).hexdigest()[:63]
        try:
            with self.session.begin():
                new_asset = PrimaryAsset(
                    display_name=asset_name,
                    organization_id=org_id,
                    kind=asset_kind,
                    repository_id=None,
                    codebase_settings_auto_commit_docs=codebase_settings_auto_commit_docs,
                )
                self.session.add(new_asset)
                primary_asset_id = new_asset.id
                new_version = Version(
                    primary_asset_id=new_asset.id,
                    display_name="Unversioned",
                    status=VersionStatus.CONNECTING,
                    previous_version_id=None,
                )
                self.session.add(new_version)
                version_id = new_version.id
                # TODO: add the creator and VersionCreator here
                relative_path = f"{new_asset.id}/{new_version.id}/{unquote_plus(file_name)}"  # TODO: don't understand what unquote_plus does here, no spaces left in filename
                upload_key = f"assets/{org_id_hash}/{relative_path}"
                asset_metadata = {
                    "unhashed_organization_id": org_id,
                    "org_name": user.organization_name,
                    "provider": "manual",
                    "version_id": str(new_version.id),
                    "asset_name": asset_name,
                    "asset_kind": new_asset.kind.value,
                }
                upload_url = generate_put_presigned_url(
                    key=upload_key,
                    content_type=content_type,
                    metadata=asset_metadata,
                )

        except IntegrityError:
            logger.error(f"Asset with name {asset_name} already exists")
            raise HTTPException(
                status_code=400, detail="Asset with this name already exists"
            )

        logger.info(f"Upload URL generated for {relative_path}")
        return UploadResponse(
            upload_url=upload_url,
            primary_asset_id=primary_asset_id,
            version_id=version_id,
        )

    def create_custom_config_and_upload_url(
        self, user: UserToken, request: UploadAutoDocConfigRequest
    ) -> UploadAutoDocConfigResponse:
        file_name = os.path.basename(request.file_path)
        content_type = "application/toml"
        if not file_name.lower().endswith(".toml"):
            raise HTTPException(status_code=400, detail="File must be a toml file")

        file_name = re.sub(r"[^a-zA-Z0-9.]", "_", file_name)
        file_name = file_name.replace(" ", "_")

        org_id = user.organization_id
        org_id_hash = hashlib.sha256(org_id.encode()).hexdigest()[:63]

        upload_key = f"{request.page_node_id}/custom_config.toml"
        asset_metadata = {
            "unhashed_organization_id": org_id,
        }
        upload_url = generate_put_presigned_url(
            key=upload_key,
            content_type=content_type,
            metadata=asset_metadata,
            bucket=org_id_hash,
        )
        return UploadAutoDocConfigResponse(
            upload_url=upload_url,
        )
