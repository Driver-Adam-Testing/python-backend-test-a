import json
import os
from datetime import datetime

import strawberry
from graphql import GraphQLError
from modal import Function
from sqlalchemy import and_, func
from sqlalchemy.future import select
from sqlmodel import Session
from strawberry.types import Info

from app.api.routes.legacy.api_types import SourceContentInput  # type: ignore
from app.api.routes.legacy.application_note import (
    ContentStatus,
)
from app.api.routes.legacy.document_set import DerivedContentTypes
from app.api.routes.legacy.s3 import S3BucketAccess
from app.api.routes.legacy.scalars import ID, JSON
from app.core.logger import logger
from driver_db.database.models_v1 import (
    Codebase,
    DerivedContent,
    DerivedContentType,
    Llm,
    SourceContent,
    SourceContentType,
    Workspace,
)


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


@strawberry.type
class Mutation:
    @strawberry.mutation
    async def create_source_content(self, info: Info, input: SourceContentInput) -> str:
        user = info.context.user
        session = info.context.session

        workspace = await session.execute(
            select(Workspace).filter_by(id=input.workspace_id)
        ).scalar_one_or_none()
        if not workspace or workspace.organization_id != user.organization_id:
            raise GraphQLError(
                "Workspace not found or access denied", extensions={"code": "FORBIDDEN"}
            )

        # TODO: Get rid of the database hits to get source and derived content types. They don't change often enough and they are limited. It's inefficient that they're defined in the database.
        source_content_type = await session.execute(
            select(SourceContentType).filter_by(type_name=input.source_content_type)
        ).first()

        if not source_content_type:
            raise GraphQLError(
                "SourceContentType not found", extensions={"code": "BAD_REQUEST"}
            )

        source_content = SourceContent(
            source_content_type_id=source_content_type.id,
            workspace_id=input.workspace_id,
            codebase_id=input.codebase_id,
            relative_path=input.relative_path,
        )
        session.add(source_content)
        session.commit()
        return str(source_content.id)

    @strawberry.mutation
    async def generateApplicationNote(
        self, info: Info, input: GenerateApplicationNoteInput
    ) -> GenerateApplicationNoteOutput:
        user = info.context.user
        session: Session = info.context.session
        codebase = session.exec(
            select(Codebase)
            .join(Workspace, Codebase.workspace_id == Workspace.id)  # type: ignore
            .where(Codebase.id == input.codebase_id)  # type: ignore
            .where(Codebase.workspace_id == input.workspace_id)  # type: ignore
            .where(Workspace.organization_id == user.organization_id)  # type: ignore
        ).first()
        if not codebase:
            raise GraphQLError(
                "Codebase not found in your organization",
                extensions={"code": "FORBIDDEN"},
            )

        llm = session.exec(select(Llm).where(Llm.model == "gpt-4-1106-preview")).first()  # type: ignore

        if not llm:
            raise GraphQLError(
                "LLM Model not found", extensions={"code": "BAD_REQUEST"}
            )

        note_content = {
            "name": "Generating Application Note...",
            "description": input.prompt,
            "content": "",
        }

        metadata = {
            "prompt": input.prompt,
            "generation_timestamp": str(datetime.now()),
            "editor_id": "",
            "description": "",
            "prompt_signature": "",
            "context": input,
            "modal_context": {"callback": {}},
            "history": [
                {
                    "action": ContentStatus.GENERATING.value,
                    "data": note_content,
                    "timestamp": str(datetime.now()),
                }
            ],
            "errors": [],
        }

        source_content: SourceContent = session.exec(
            select(SourceContent.id)  # type: ignore
            .join(
                SourceContentType,
                SourceContent.source_content_type_id == SourceContentType.id,
            )
            .where(
                SourceContent.codebase_id == input.codebase_id,
                SourceContentType.type_name == "codebase",
            )
        ).first()
        derived_content_type_id = (
            session.exec(
                select(DerivedContentType.id).where(  # type: ignore
                    DerivedContentType.type_name
                    == DerivedContentTypes.APPLICATION_NOTE.value  # type: ignore
                )
            )
            .all()[0]
            .id
        )
        app_note = DerivedContent(
            source_content_id=source_content.id,
            derived_content_type_id=derived_content_type_id,
            content=json.dumps(note_content),
            status=ContentStatus.GENERATING.value,
            llm_id=None,
            metadata=metadata,
        )

        session.add(app_note)
        session.commit()

        ## NOTE: This is a major change, we skip the comprehneder api entirely.
        app_note_func = Function.lookup("comprehender", "create_app_note")
        call = app_note_func.spawn(
            input.workspace_id, source_content.id, input.prompt, None, None
        )
        if call is None:
            raise GraphQLError(
                "Failed to spawn app note function call.",
                extensions={"code": "INTERNAL_SERVER_ERROR"},
            )
        return GenerateApplicationNoteOutput(id=str(call.object_id))

    @strawberry.mutation
    async def generateApplicationNoteEdit(
        self, info: Info, input: ApplicationNoteEditInput
    ) -> GenerateApplicationNoteEditOutput:
        # NOTE: This is being called regardless of appnote or techdoc situations.
        user = info.context.user
        session = info.context.db

        note = session.exec(
            select(DerivedContent)
            .join(SourceContent, DerivedContent.source_content)  # type: ignore
            .join(Codebase, SourceContent.codebase)  # type: ignore
            .join(Workspace, Codebase.workspace)  # type: ignore
            .where(
                DerivedContent.id == input.id,  # type: ignore
                Workspace.organization_id == user.organization_id,  # type: ignore
            )
        ).first()

        if not note:
            raise GraphQLError(
                "Application Notes not found.", extensions={"code": "BAD_REQUEST"}
            )

        app_note_func = Function.lookup("comprehender", "single_shot_edit")
        call = app_note_func.spawn(input.workspace_id, input.id, input.prompt, None)
        if call is None:
            raise GraphQLError(
                "Failed to initiate application note edit process.",
                extensions={"code": "INTERNAL_SERVER_ERROR"},
            )
        return GenerateApplicationNoteEditOutput(
            call_id=call.object_id, status=ContentStatus.GENERATING.value
        )

    @strawberry.mutation
    def updateApplicationNote(
        self, info: Info, input: UpdateApplicationNoteInput
    ) -> None:
        session = info.context.session
        user = info.context.user

        try:
            note = (
                session.query(DerivedContent)
                .filter(DerivedContent.id == input.id)
                .join(SourceContent)
                .join(Codebase)
                .join(Workspace)
                .filter(Workspace.organization_id == user.organization_id)
                .one_or_none()
            )

            if not note:
                raise GraphQLError(
                    "Application note not found", extensions={"code": "BAD_REQUEST"}
                )

            def escape_html(obj):
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
    async def deleteApplicationNote(self, info: Info, id: ID | None = None) -> None:
        session = info.context.session
        try:
            note = session.exec(
                select(DerivedContent).where(
                    DerivedContent.id == id,  # type: ignore
                    DerivedContent.derived_content_type.has(  # type: ignore
                        type_name=DerivedContentTypes.APPLICATION_NOTE.value
                    ),
                )
            ).scalar_one_or_none()

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

        # Check if the workspace exists
        workspace_exists = (
            session.exec(
                select(func.count())
                .select_from(Workspace)
                .where(
                    and_(
                        Workspace.id == workspace_id,  # type: ignore
                        Workspace.organization_id == org_id,  # type: ignore
                    )
                )
            ).scalar_one()
            > 0
        )

        if not workspace_exists:
            raise GraphQLError(
                "Workspace not found", extensions={"code": "BAD_REQUEST"}
            )

        try:
            s3_access = S3BucketAccess(organization_id=org_id, codebase_id=codebase_id)
            relative_path = os.path.basename(file_path)
            upload_url = s3_access.get_signed_upload_url(relative_path=relative_path)
            logger.info(f"Upload URL generated for {relative_path}")
            return upload_url
        except Exception as e:
            logger.error(
                f"Error generating upload URL for {relative_path}: {e}", exc_info=True
            )
            raise GraphQLError(
                "Upload URL not created.", extensions={"code": "BAD_REQUEST"}
            )

    @strawberry.mutation
    async def generateDocumentEdit(
        self, info: Info, input: DocumentEditInput
    ) -> GenerateApplicationNoteEditOutput:
        user = info.context.user
        session = info.context.session

        if not user or not user.organization_id:
            raise GraphQLError(
                "Invalid user or organization ID", extensions={"code": "BAD_REQUEST"}
            )
        codebase = session.exec(
            select(Codebase).where(
                Codebase.id == input.codebase_id,  # type: ignore
                Codebase.workspace_id == input.workspace_id,  # type: ignore
            )
        ).first()
        if not codebase:
            raise GraphQLError("Codebase not found", extensions={"code": "BAD_REQUEST"})

        workspace = session.exec(
            select(Workspace).where(
                Workspace.id == input.workspace_id,  # type: ignore
                Workspace.organization_id == user.organization_id,  # type: ignore
            )
        ).first()
        if not workspace:
            raise GraphQLError(
                "Workspace does not belong to the user's organization.",
                extensions={"code": "FORBIDDEN"},
            )

        techDoc = session.exec(
            select(DerivedContent).where(DerivedContent.id == input.document_id)  # type: ignore
        ).first()
        if not techDoc:
            raise GraphQLError(
                "Document not found.", extensions={"code": "BAD_REQUEST"}
            )

        try:
            single_shot_edit = Function.lookup("comprehender", "single_shot_edit")
            call = single_shot_edit.spawn(
                input.workspace_id, input.codebase_id, None, input.options
            )
            if call is None:
                raise GraphQLError(
                    "Failed to initiate document edit process.",
                    extensions={"code": "INTERNAL_SERVER_ERROR"},
                )
            return GenerateApplicationNoteEditOutput(
                call_id=call.object_id, status=ContentStatus.GENERATING.value
            )
        except Exception as error:
            logger.error(f"Error generating document edit: {error}", exc_info=True)
            raise GraphQLError(
                "Document edit not created",
                extensions={"code": "BAD_REQUEST", "message": "Document edit failed."},
            )
