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
from sqlalchemy.exc import IntegrityError

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
    generate_put_presigned_url,
    org_id_to_hash,
)


class UploadService:
    def __init__(self, session: CurrentSession) -> None:
        self.session = session
        self.asset_repository = BaseRepository(session, PrimaryAsset)

    def create_codebase_and_upload_url(
        self, user: UserToken, request: UploadCodebaseRequest
    ) -> UploadResponse:
        logger.info(
            f"upload_codebase called with request: {request} for organization_id: {user.organization_id}"
        )

        file_path = request.file_path
        organization_id = user.organization_id
        codebase_name = os.path.splitext(os.path.basename(file_path))[0]

        try:
            with self.session.begin():
                # We create the primary asset here with status == CONNECTING
                # There is potential for this to get stuck in connecting state, if the upload fails (e.g. firewall issue)
                # In that case, the user will need to delete the primary asset before reattempting the upload
                # TODO: future optimization, check for CONNECTION_FAILED and delete the old primary asset
                new_asset = PrimaryAsset(
                    display_name=codebase_name,
                    organization_id=organization_id,
                    kind=PrimaryAssetKind.CODEBASE,
                    repository_id=None,
                )
                self.session.add(new_asset)
                new_version = Version(
                    primary_asset_id=new_asset.id,
                    display_name="Unversioned",
                    status=VersionStatus.CONNECTING,
                    previous_version_id=None,
                )
                self.session.add(new_version)
        except IntegrityError:
            logger.error(f"Asset with name {codebase_name} already exists")
            raise HTTPException(
                status_code=400, detail="Codebase with this name already exists"
            )

        org_id_hash = org_id_to_hash(organization_id)
        upload_key = f"codebases/{org_id_hash}/{os.path.basename(file_path)}"

        logger.info(f"Upload URL generated for {upload_key}")
        codebase_metadata = {
            "unhashed_organization_id": organization_id,
            "org_name": user.organization_name,
            "provider": "manual",
            "version_id": str(new_version.id),
        }

        upload_url = generate_put_presigned_url(
            key=upload_key,
            content_type="application/zip",
            metadata=codebase_metadata,
        )

        return UploadResponse(upload_url=upload_url)

    def upload_pdf(
        self, user: UserToken, request: UploadPDFRequest
    ) -> PDFUploadResponse:
        original_file_name = os.path.basename(request.file_path)

        existing_asset = self.asset_repository.get_by_conditions(
            [
                PrimaryAsset.display_name == original_file_name,
                PrimaryAsset.organization_id == user.organization_id,
            ]
        )
        if existing_asset is not None:
            logger.warn(f"Existing doc found with name: {original_file_name}")
            raise HTTPException(
                status_code=400, detail="Document with this name already exists"
            )

        file_name = re.sub(r"[^a-zA-Z0-9.]", "_", original_file_name)
        file_name = file_name.replace(" ", "_")
        file_name = f"{uuid4()}_{file_name}"

        relative_path = unquote_plus(file_name)  # sanitize and make safe for s3 upload

        creator_id = user.user_id
        org_id = user.organization_id

        logger.info(f"Uploading content for orgId: {org_id}, ownerId: {creator_id}")

        try:
            org_id_hash = hashlib.sha256(org_id.encode()).hexdigest()[:63]
            # For the dropzone upload, we overwrite anything with the same name, we'll version the file
            # when we move to the org bucket
            upload_key = f"documents/{org_id_hash}/{relative_path}"

            # with self.session.begin():
            # TODO: a transaction is already in progress at this point, so we can't start another
            # I'm not sure why a transaction is already in progress?
            new_asset = PrimaryAsset(
                display_name=original_file_name,
                organization_id=org_id,
                kind=PrimaryAssetKind.FILE,
            )
            self.session.add(new_asset)

            new_version = Version(
                primary_asset_id=new_asset.id,
                display_name="v1",
                status=VersionStatus.GENERATING,
            )
            self.session.add(new_version)

            new_node = Node(
                kind=NodeKind.OTHER,
                version_id=new_version.id,
                relative_path=relative_path,
            )
            self.session.add(new_node)
            self.session.commit()

            pdf_metadata = {
                "organization_id": org_id,
                "org_bucket": org_id_hash,
                "org_name": user.organization_name,
                "creator_id": creator_id,
                "file_path": relative_path,
                "content_type": "supplemental-document",
                "node_id": str(new_node.id),
                "version_id": str(new_version.id),
                "primary_asset_id": str(new_asset.id),
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
