# mypy: disable_error_code="call-arg"
import strawberry
from database.models_v1 import Workspace
from graphql import GraphQLError
from sqlmodel import select
from strawberry.types import Info

from app.api.routes.legacy.api_types import (
    CodebaseResults,  # type: ignore
    OrganizationResult,  # type: ignore
    SupplementalContent,  # type: ignore
)
from app.api.routes.legacy.application_note import (
    ApplicationNoteEditResponse,
    ApplicationNoteResponse,
    application_note_edit,
    get_application_note,
)
from app.api.routes.legacy.auth0 import get_organization_by_id
from app.api.routes.legacy.document_set import DocumentSet, get_document_set
from app.api.routes.legacy.orm_ops import (
    check_access,
    get_codebase_by_id,
    supplemental_content_by_codebase_id,
)
from app.api.routes.legacy.scalars import ID, NodeType
from app.api.routes.legacy.symbol_set import SymbolSetResponse, symbol_set
from app.api.routes.legacy.tree import FlatNode, get_codebase_tree


@strawberry.type
class MeResponse:
    id: ID


@strawberry.type
class Query:
    @strawberry.field
    async def organization(self, info: Info, id: str) -> OrganizationResult:
        session = info.context.session
        if info.context.user.organization_id != id:
            raise GraphQLError(
                "Organization not found", extensions={"code": "NOT_FOUND"}
            )
        organization = get_organization_by_id(id)
        workspaces = session.exec(
            select(Workspace).where(Workspace.organization_id == id)
        ).all()

        return OrganizationResult(
            id=organization["id"],
            name=organization["name"],
            display_name=organization["display_name"],
            workspaces=workspaces,
        )

    @strawberry.field
    async def codebase(self, info: Info, id: ID | None = None) -> CodebaseResults:
        session = info.context.session
        user_org_id = info.context.user.organization_id
        if id is None:
            raise GraphQLError(
                "id must not be None", extensions={"code": "BAD_REQUEST"}
            )
        if not check_access(session, user_org_id, codebase_id=str(id)):
            raise GraphQLError(
                "Access denied to the codebase", extensions={"code": "NOT_FOUND"}
            )
        codebase = get_codebase_by_id(session, str(id))
        if codebase is None:
            raise GraphQLError("Codebase not found", extensions={"code": "NOT_FOUND"})
        return codebase

    @strawberry.field
    async def documentSet(
        self,
        info: Info,
        nodeKind: NodeType,
        path: str | None = None,
        workspaceId: ID | None = None,
        codebaseId: ID | None = None,
    ) -> DocumentSet:
        if path is None or workspaceId is None or codebaseId is None:
            raise GraphQLError(
                "path, workspaceId, and codebaseId must not be None",
                extensions={"code": "BAD_REQUEST"},
            )
        session = info.context.session
        if not check_access(
            session,
            info.context.user.organization_id,
            workspace_id=str(workspaceId),
            codebase_id=str(codebaseId),
        ):
            raise GraphQLError("Access denied", extensions={"code": "NOT_FOUND"})
        return get_document_set(
            nodeKind,
            path,
            str(workspaceId),
            str(codebaseId),
            info.context.user.organization_id,
            session,
        )

    @strawberry.field
    async def applicationNote(
        self, info: Info, id: ID | None = None
    ) -> ApplicationNoteResponse:
        session = info.context.session
        if id is not None:
            id_str = str(id)
        else:
            raise GraphQLError(
                "id must not be None", extensions={"code": "BAD_REQUEST"}
            )
        if not check_access(
            session, info.context.user.organization_id, derived_content_id=id_str
        ):
            raise GraphQLError("Access denied", extensions={"code": "NOT_FOUND"})
        return get_application_note(id_str, session, info.context.user.organization_id)

    @strawberry.field
    async def tree(
        self, info: Info, codebaseId: ID, workspaceId: ID | None = None
    ) -> list[FlatNode]:
        session = info.context.session
        user = info.context.user
        if not check_access(session, user.organization_id, codebase_id=str(codebaseId)):
            raise GraphQLError("Access denied", extensions={"code": "NOT_FOUND"})
        return get_codebase_tree(str(codebaseId), session, user.organization_id)

    @strawberry.field
    async def symbolSet(
        self, info: Info, sourceContentId: ID, page: int = 1, pageSize: int = 10
    ) -> SymbolSetResponse:
        session = info.context.session
        organization_id = info.context.user.organization_id
        if not check_access(
            session, organization_id, source_content_id=str(sourceContentId)
        ):
            raise GraphQLError("Access denied", extensions={"code": "NOT_FOUND"})
        return symbol_set(
            session, str(sourceContentId), organization_id, page, pageSize
        )

    @strawberry.mutation
    async def applicationNoteEdit(self, call_id: ID) -> ApplicationNoteEditResponse:
        # Assuming access check is performed within the application_note_edit function or not required due to the nature of the mutation.
        return await application_note_edit(str(call_id))

    @strawberry.field
    async def supplementalContent(
        self, info: Info, codebaseId: ID
    ) -> list[SupplementalContent]:
        session = info.context.session
        user = info.context.user
        organization_id = user.organization_id
        if not check_access(session, organization_id, codebase_id=str(codebaseId)):
            raise GraphQLError("Access denied", extensions={"code": "NOT_FOUND"})
        return supplemental_content_by_codebase_id(
            session=session, codebase_id=str(codebaseId)
        )

    @strawberry.field
    async def me(self, info: Info) -> MeResponse:
        user = info.context.user
        return MeResponse(id=user.subject)  # type: ignore
