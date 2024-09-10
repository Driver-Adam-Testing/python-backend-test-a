import hashlib
import os
import re
from urllib.parse import unquote_plus
from uuid import uuid4

from database.models_v1 import DerivedContent
from fastapi import HTTPException

from app.api.auth import CurrentUser
from app.api.session import CurrentSession
from app.core.logger import logger
from app.repositories.base_repository import BaseRepository
from app.repositories.derived_content_type_repository import (
    DerivedContentTypeRepository,
)
from app.repositories.workspace_repository import WorkspaceRepository
from app.schemas.upload_schema import (
    DirectUploadResponse,
    UploadCodebaseRequest,
    UploadPDFRequest,
    UploadResponse,
)
from app.utils.aws_s3 import (
    generate_put_presigned_url,
)


class UploadService:
    def __init__(self, session: CurrentSession):
        self.session = session
        self.workspace_repository = WorkspaceRepository(session)
        self.content_repository = BaseRepository(session, DerivedContent)
        self.derived_content_repository = DerivedContentTypeRepository(session)

    def upload_codebase(
        self, user: CurrentUser, request: UploadCodebaseRequest
    ) -> UploadResponse:
        logger.info(
            f"upload_codebase called with request: {request} for organization_id: {user.organization_id}"
        )

        default_workspace = self.workspace_repository.get_default_workspace(
            user.organization_id
        )
        if not default_workspace:
            raise HTTPException(status_code=400, detail="Default workspace not found")

        workspace_id = str(default_workspace.id)
        file_path = request.file_path
        creator_id = user.user_id
        organization_id = user.organization_id
        codebase_name = os.path.splitext(os.path.basename(file_path))[0]

        try:
            org_id_hash = hashlib.sha256(organization_id.encode()).hexdigest()[:63]
            upload_key = f"codebases/{org_id_hash}/{os.path.basename(file_path)}"

            logger.info(f"Upload URL generated for {upload_key}")
            codebase_metadata = {
                "organization_id": org_id_hash,
                "org_bucket": org_id_hash,
                "org_name": user.organization_name,
                "workspace_id": workspace_id,
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
        except Exception as e:
            logger.error(f"Error uploading codebase: {e}")
            raise HTTPException(status_code=500, detail="Error uploading codebase")

        return UploadResponse(upload_url=upload_url)

    def upload_pdf(
        self, user: CurrentUser, request: UploadPDFRequest
    ) -> UploadResponse:
        # check for dups
        # mint url to upload pdf direct to org bucket
        # mint derived content if not a dup in processing status with url attached
        # UI handles upload to s3 if it fails it delete the derived content record
        # if it succeeds it updates the derived content record to processing complete
        file_path = request.file_path
        creator_id = user.user_id
        org_id = user.organization_id
        logger.info(f"Uploading content for orgId: {org_id}, ownerId: {creator_id}")

        default_workspace = self.workspace_repository.get_default_workspace(
            user.organization_id
        )
        if not default_workspace:
            raise HTTPException(status_code=400, detail="Default workspace not found")

        workspace_id = str(default_workspace.id)
        try:
            relative_path = os.path.basename(file_path)
            org_id_hash = hashlib.sha256(org_id.encode()).hexdigest()[:63]
            # Upload the PDF to the S3 bucket documents folder not the codebases folder
            upload_key = f"documents/{org_id_hash}/{os.path.basename(file_path)}"
            codebase_metadata = {
                "organization_id": org_id,
                "org_bucket": org_id_hash,
                "org_name": user.organization_name,
                "workspace_id": workspace_id,
                "creator_id": creator_id,
                "file_path": file_path,
                "content_type": "supplemental-document",
            }
            upload_url = generate_put_presigned_url(
                key=upload_key,
                content_type="application/pdf",
                metadata=codebase_metadata,
            )
            logger.info(f"Upload URL generated for {relative_path}")
            return UploadResponse(upload_url=upload_url)
        except Exception as e:
            logger.error(f"Error uploading PDF: {e}")
            raise HTTPException(status_code=500, detail="Error uploading PDF")

    def direct_upload_pdf(
        self, user: CurrentUser, request: UploadPDFRequest
    ) -> DirectUploadResponse:
        # check for dups
        # mint url to upload pdf direct to org bucket
        # mint derived content if not a dup in processing status with url attached
        # UI handles upload to s3 if it fails it delete the derived content record
        # if it succeeds it updates the derived content record to processing complete
        default_workspace = self.workspace_repository.get_default_workspace(
            user.organization_id
        )
        if not default_workspace:
            raise HTTPException(status_code=400, detail="Default workspace not found")

        existing_doc_count = self.content_repository.count_by(
            [
                DerivedContent.content_name == os.path.basename(request.file_path),
                DerivedContent.workspace_id == default_workspace.id,
            ]
        )
        if existing_doc_count > 0:
            raise HTTPException(
                status_code=400, detail="Document with this name already exists"
            )
        print(f"existing docs found: {existing_doc_count}")

        original_file_name = os.path.basename(request.file_path)

        # file_parts = os.path.basename(request.file_path).split(".")
        # file_parts
        # file_name = file_parts[0]
        # file_extension = file_parts[len(file_parts) - 1]
        file_name = re.sub(r"[^a-zA-Z0-9.]", "_", os.path.basename(request.file_path))
        file_name = file_name.replace(" ", "_")
        file_name = f"{uuid4()}_{file_name}"

        relative_path = unquote_plus(file_name)  # sanitize and make safe for s3 upload
        print(relative_path)

        # sanitize and make safe for s3 upload
        creator_id = user.user_id
        org_id = user.organization_id

        logger.info(f"Uploading content for orgId: {org_id}, ownerId: {creator_id}")

        workspace_id = str(default_workspace.id)
        try:
            org_id_hash = hashlib.sha256(org_id.encode()).hexdigest()[:63]
            # Upload the PDF to the S3 bucket documents folder not the codebases folder
            upload_key = f"documents/{org_id_hash}/{relative_path}"

            content_type = self.derived_content_repository.get_by_type_name(
                "supplemental-document"
            )
            new_document = self.content_repository.create(
                DerivedContent(
                    content_name=original_file_name,
                    workspace_id=default_workspace.id,
                    relative_path=relative_path,
                    content_type_id=content_type.id,
                    status="generating",
                )
            )

            codebase_metadata = {
                "organization_id": org_id,
                "org_bucket": org_id_hash,
                "org_name": user.organization_name,
                "workspace_id": workspace_id,
                "creator_id": creator_id,
                "file_path": relative_path,
                "content_type": "supplemental-document",
                "source_content_id": str(new_document.id),
            }
            upload_url = generate_put_presigned_url(
                key=upload_key,
                content_type="application/pdf",
                metadata=codebase_metadata,
            )

            logger.info(f"Upload URL generated for {relative_path}")
            return DirectUploadResponse(
                upload_url=upload_url, source_content_id=new_document.id
            )
        except Exception as e:
            logger.error(f"Error uploading PDF: {e}")
            raise HTTPException(status_code=500, detail="Error uploading PDF")
