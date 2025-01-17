import hashlib
import json
import os

import strawberry
from app.api.routes.legacy.orm_ops import (
    check_access,
    get_derived_content_by_id,
)
from app.api.routes.legacy.scalars import ID, JSON
from app.core.logger import logger
from app.utils.aws_s3 import generate_put_presigned_url
from database.models_v1 import (
    DerivedContent,
)
from database.models_v2 import Node, PrimaryAsset, Version
from graphql import GraphQLError
from strawberry.types import Info


@strawberry.type
class GenerateApplicationNoteOutput:
    id: str


@strawberry.type
class GenerateApplicationNoteEditOutput:
    call_id: str
    status: str


@strawberry.type
class UpdateApplicationNoteOutput:
    success: bool


@strawberry.type
class DeleteApplicationNoteOutput:
    success: bool


@strawberry.type
class WebhookOutput:
    document_id: str


@strawberry.type
class UploadSourceContentOutput:
    upload_url: str


@strawberry.input
class UpdateApplicationNoteInput:
    id: ID
    content: str | None = None
    name: str | None = None


@strawberry.input
class UpdateDocumentInput:
    id: ID
    content: str | None = None
    name: str | None = None


@strawberry.input
class GenerateApplicationNoteInput:
    codebase_id: ID
    workspace_id: ID
    prompt: str
    editor_id: str | None = None
    organization_id: str | None = None


@strawberry.input
class ApplicationNoteEditInput:
    id: ID
    prompt: str
    workspace_id: ID


@strawberry.input
class DocumentEditInput:
    document_id: ID
    workspace_id: ID
    codebase_id: ID
    options: JSON  # type: ignore


@strawberry.input
class UploadCodebaseInput:
    workspace_id: str
    file_path: str


@strawberry.input
class WebhookInput:
    content: str | None = None
    document_id: ID
    errors: list[str | None] | None = None
    extra_context: JSON | None = None  # type: ignore
    name: str | None = None
    prompt: str


@strawberry.type
class Mutation:
    @strawberry.mutation
    def updateApplicationNote(
        self, info: Info, input: UpdateApplicationNoteInput
    ) -> None:
        session = info.context.session
        user = info.context.user
        if not check_access(session, user.organization_id, derived_content_id=input.id):
            raise GraphQLError("Access denied", extensions={"code": "FORBIDDEN"})

        try:
            note = get_derived_content_by_id(session, input.id)
            if not note:
                raise GraphQLError(
                    "Application note not found", extensions={"code": "BAD_REQUEST"}
                )

            def escape_html(obj: str) -> str:
                return (
                    obj.replace("&", "&amp;")
                    .replace("<", "&lt;")
                    .replace(">", "&gt;")
                    .replace('"', "&quot;")
                    .replace("'", "&#039;")
                )

            sanitized_name = escape_html(input.name) if input.name else ""
            sanitized_content = escape_html(input.content) if input.content else ""

            note_content = json.loads(note.content)
            if sanitized_name:
                note_content["name"] = sanitized_name
            if sanitized_content:
                note_content["content"] = sanitized_content
            note.content = json.dumps(note_content)

            session.add(note)
            session.commit()

            return None
        except Exception as e:
            session.rollback()
            logger.error(
                f"Error updating application note {input.id}: {e}", exc_info=True
            )
            raise GraphQLError(
                "Application note update failed", extensions={"code": "BAD_REQUEST"}
            )

    @strawberry.mutation
    def deleteApplicationNote(self, info: Info, id: ID | None = None) -> None:
        session = info.context.session
        user = info.context.user
        if not check_access(session, user.organization_id, derived_content_id=id):
            raise GraphQLError("Access denied", extensions={"code": "FORBIDDEN"})
        try:
            note = get_derived_content_by_id(session, id)
            if not note:
                raise GraphQLError(
                    "Application note not found", extensions={"code": "BAD_REQUEST"}
                )

            session.delete(note)
            session.commit()

            return None
        except Exception as e:
            logger.error(f"Error deleting application note {id}: {e}", exc_info=True)
            raise GraphQLError(
                "Application note not deleted", extensions={"code": "BAD_REQUEST"}
            )

    @strawberry.input
    class UploadContentInput:
        codebase_id: str
        workspace_id: str
        file_path: str

    @strawberry.mutation
    def uploadSourceContent(self, info: Info, input: UploadContentInput) -> str:
        workspace_id = input.workspace_id
        codebase_id = input.codebase_id
        file_path = input.file_path
        user = info.context.user
        session = info.context.session
        creator_id = user.user_id
        org_id = user.organization_id
        logger.info(
            f"Uploading content for orgId: {org_id}, workspaceId: {workspace_id}, ownerId: {creator_id}"
        )

        if not codebase_id or not file_path or not workspace_id or not creator_id:
            raise GraphQLError("Invalid Request", extensions={"code": "BAD_REQUEST"})
        if not check_access(session, org_id, codebase_id=codebase_id):
            raise GraphQLError(
                "Access denied to the codebase", extensions={"code": "FORBIDDEN"}
            )

        try:
            relative_path = os.path.basename(file_path)
            org_id_hash = hashlib.sha256(org_id.encode()).hexdigest()[:63]
            upload_key = f"documents/{org_id_hash}/{os.path.basename(file_path)}"
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
            return upload_url
        except Exception as e:
            logger.error(
                f"Error generating upload URL for {relative_path}: {e}", exc_info=True
            )
            raise GraphQLError(
                "Upload URL not created.", extensions={"code": "BAD_REQUEST"}
            )

    # NOTE: Not dry. same as updateApplicationNote

    @strawberry.mutation
    def updateDocument(self, info: Info, input: UpdateDocumentInput) -> None:
        session = info.context.session
        user = info.context.user

        try:
            note = (
                session.query(DerivedContent)
                .filter(DerivedContent.id == input.id)
                .join(Node)
                .join(Version)
                .join(PrimaryAsset)
                .where(PrimaryAsset.organization_id == user.organization_id)
                .one_or_none()
            )

            if not note:
                raise GraphQLError(
                    "Application note not found", extensions={"code": "BAD_REQUEST"}
                )

            note.content = input.content

            session.add(note)
            session.commit()

            return None
        except Exception as e:
            session.rollback()
            logger.error(
                f"Error updating application note {input.id}: {e}", exc_info=True
            )
            raise GraphQLError(
                "Application note update failed", extensions={"code": "BAD_REQUEST"}
            )

    @strawberry.mutation
    def uploadCodebase(self, info: Info, input: UploadCodebaseInput) -> str:
        user = info.context.user
        workspace_id = input.workspace_id
        file_path = input.file_path
        creator_id = user.user_id
        org_id = user.organization_id
        codebase_name = os.path.splitext(os.path.basename(file_path))[0]

        logger.info(
            f"Uploading codebase for orgId: {org_id}, workspaceId: {workspace_id}, ownerId: {creator_id}"
        )

        if (
            not codebase_name
            or not file_path
            or not org_id
            or not workspace_id
            or not creator_id
        ):
            raise GraphQLError("Invalid Request", extensions={"code": "BAD_REQUEST"})

        # TODO: Complete validations
        # # Check if the workspace exists
        # workspace_exists = db_session.query(Workspace).filter(and_(
        #     Workspace.id == workspace_id,
        #     Workspace.organization_id == org_id
        # )).count() > 0

        # if not workspace_exists:
        #     raise GraphQLError("Workspace not found", extensions={"code": "BAD_REQUEST"})

        # # Validate that the name is unique within the org
        # is_name_unique = db_session.query(Codebase).filter(and_(
        #     Codebase.workspace_id == workspace_id,
        #     Codebase.codebase_name == codebase_name
        # )).count() == 0

        # if not is_name_unique:
        #     raise GraphQLError("Resource name already exists.", extensions={"code": "BAD_REQUEST"})

        try:
            org_id_hash = hashlib.sha256(org_id.encode()).hexdigest()[:63]
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
            upload_url = generate_put_presigned_url(
                key=upload_key,
                content_type="application/zip",
                metadata=codebase_metadata,
            )
            return upload_url
        except Exception as e:
            logger.error(f"Error generating upload URL for {upload_key}: {e}")
            raise GraphQLError(
                "Upload URL not created.", extensions={"code": "BAD_REQUEST"}
            )

    # TODO: add create embeddings and create_source content
    # TODO: Change readme to reflect current alembic flow
    # TODO: Audit all error handling
    # TODO: Create a db wrapper that controls all org_id forbidden checks.
    # TODO: Check for eaasier ways to do all the enum fetching
