import hashlib
import os
import re
from urllib.parse import unquote_plus
from uuid import uuid4

from database.models_v2 import (
    Node,
    PrimaryAsset,
    Version,
)
from database.models_v2_enums import (
    NodeKind,
    PrimaryAssetKind,
    VersionStatus,
)
from fastapi import HTTPException

from app.api.auth import UserToken
from app.api.session import CurrentSession
from app.core.logger import logger
from app.repositories.base_repository import BaseRepository
from app.schemas.upload_schema import (
    PDFUploadResponse,
    UploadCodebaseRequest,
    UploadPDFRequest,
    UploadResponse,
)
from app.utils.aws_s3 import (
    generate_get_presigned_url,
    generate_put_presigned_url,
    org_id_to_hash,
)


class UploadService:
    def __init__(self, session: CurrentSession) -> None:
        self.session = session
        self.asset_repository = BaseRepository(session, PrimaryAsset)
        self.version_repository = BaseRepository(session, Version)
        self.node_repository = BaseRepository(session, Node)

    def upload_codebase(
        self, user: UserToken, request: UploadCodebaseRequest
    ) -> UploadResponse:
        logger.info(
            f"upload_codebase called with request: {request} for organization_id: {user.organization_id}"
        )

        file_path = request.file_path
        creator_id = user.user_id
        organization_id = user.organization_id
        codebase_name = os.path.splitext(os.path.basename(file_path))[0]

        try:
            org_id_hash = org_id_to_hash(organization_id)
            upload_key = f"analysis/{org_id_hash}/{os.path.basename(file_path)}"

            logger.info(f"Upload URL generated for {upload_key}")
            codebase_metadata = {
                "organization_id": org_id_hash,
                "org_bucket": org_id_hash,
                "org_name": user.organization_name,
                "creator_id": creator_id,
                "file_path": file_path,
                "codebase_name": codebase_name,
                "content_type": "codebase",
                "provider": "manual",
            }

            upload_url = generate_put_presigned_url(
                key=upload_key,
                content_type="application/zip",
                metadata=codebase_metadata,
            )
            download_url = generate_get_presigned_url(
                key=upload_key,
            )
        except Exception as e:
            logger.error(f"Error uploading codebase: {e}")
            raise HTTPException(status_code=500, detail="Error uploading codebase")

        return UploadResponse(upload_url=upload_url, download_url=download_url)

    def upload_pdf(
        self, user: UserToken, request: UploadPDFRequest
    ) -> PDFUploadResponse:
        original_file_name = os.path.basename(request.file_path)

        # TODO: Now we create a new version instead of not processing, but perhaps we can include
        # a warning that a document of this name already exists?
        # TODO: or check if the document is identical to exisitng and skip processing in that case
        existing_asset = self.asset_repository.get_by_conditions(
            [
                PrimaryAsset.display_name == original_file_name,
                PrimaryAsset.organization_id == user.organization_id,
            ]
        )
        # if existing_doc_count > 0:
        #     logger.warn(f"Existing doc found with name: {original_file_name}")
        #     raise HTTPException(
        #         status_code=400, detail="Document with this name already exists"
        #     )

        file_name = re.sub(r"[^a-zA-Z0-9.]", "_", original_file_name)
        file_name = file_name.replace(" ", "_")
        file_name = f"{uuid4()}_{file_name}"  # TODO: idk why we add this uuid here, not attached to any db entity

        relative_path = unquote_plus(file_name)  # sanitize and make safe for s3 upload

        creator_id = user.user_id
        org_id = user.organization_id

        logger.info(f"Uploading content for orgId: {org_id}, ownerId: {creator_id}")

        try:
            org_id_hash = hashlib.sha256(org_id.encode()).hexdigest()[:63]
            # For the dropzone upload, we overwrite anything with the same name, we'll version the file
            # when we move to the org bucket
            upload_key = f"documents/{org_id_hash}/{relative_path}"

            if not existing_asset:
                new_asset = self.asset_repository.create(
                    PrimaryAsset(
                        display_name=original_file_name,
                        organization_id=org_id,
                        kind=PrimaryAssetKind.FILE,
                    )
                )
                asset_id = new_asset.id
                previous_versions_count = 0
            else:
                asset_id = existing_asset.id
                previous_versions_count = self.version_repository.count_by(
                    [Version.primary_asset_id == asset_id]
                )

            new_version = self.version_repository.create(
                Version(
                    primary_asset_id=asset_id,
                    display_name=f"v{previous_versions_count + 1}",
                    status=VersionStatus.GENERATING,
                )
            )

            new_node = self.node_repository.create(
                Node(
                    kind=NodeKind.OTHER,
                    version_id=new_version.id,
                    relative_path=relative_path,
                )
            )

            pdf_metadata = {
                "organization_id": org_id,
                "org_bucket": org_id_hash,
                "org_name": user.organization_name,
                "creator_id": creator_id,
                "file_path": relative_path,
                "content_type": "supplemental-document",
                "node_id": str(new_node.id),
                "version_id": str(new_version.id),
                "primary_asset_id": str(asset_id),
            }
            upload_url = generate_put_presigned_url(
                key=upload_key,
                content_type="application/pdf",
                metadata=pdf_metadata,
            )

            logger.info(f"Upload URL generated for {relative_path}")
            return PDFUploadResponse(upload_url=upload_url, node_id=new_node.id)
        except Exception as e:
            logger.error(f"Error uploading PDF: {e}")
            raise HTTPException(status_code=500, detail="Error uploading PDF")
