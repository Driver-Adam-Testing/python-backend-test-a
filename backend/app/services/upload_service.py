import hashlib
import os

from fastapi import HTTPException

from app.api.auth import CurrentUser
from app.api.session import CurrentSession
from app.core.logger import logger
from app.repositories.workspace_repository import WorkspaceRepository
from app.schemas.upload_schema import (
    UploadCodebaseRequest,
    UploadPDFRequest,
    UploadResponse,
)
from app.utils.aws_s3 import generate_put_presigned_url


class UploadService:
    def __init__(self, session: CurrentSession):
        self.session = session
        self.workspace_repository = WorkspaceRepository(session)

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
            # upload_key = self.get_file_path(codebase_id, relative_path)

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
        workspace_id = request.workspace_id
        codebase_id = request.codebase_id
        file_path = request.file_path
        creator_id = user.user_id
        org_id = user.organization_id
        logger.info(
            f"Uploading content for orgId: {org_id}, workspaceId: {workspace_id}, ownerId: {creator_id}"
        )

        if not codebase_id or not file_path or not workspace_id or not creator_id:
            raise HTTPException(status_code=400, detail="Invalid Request")

        try:
            relative_path = os.path.basename(file_path)
            org_id_hash = hashlib.sha256(org_id.encode()).hexdigest()[:63]
            upload_key = f"documents/{org_id_hash}/{os.path.basename(file_path)}"
            # upload_key = self.get_file_path(
            #     codebase_id, relative_path, prefix="/documents"
            # )
            codebase_metadata = {
                "organization_id": org_id_hash,
                "org_bucket": org_id_hash,
                "org_name": user.organization_name,
                "workspace_id": workspace_id,
                "codebase_id": codebase_id,
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
