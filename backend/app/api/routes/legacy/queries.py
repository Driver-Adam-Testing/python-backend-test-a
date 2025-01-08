# mypy: disable_error_code="call-arg"
import logging
from datetime import datetime

import strawberry
from app.api.routes.legacy.api_types import (
    CodebaseResults,  # type: ignore
    GitProvider,
    GitRepository,
    OrganizationResult,  # type: ignore
)
from app.api.routes.legacy.application_note import (
    ApplicationNoteEditResponse,
    ApplicationNoteResponse,
    application_note_edit,
    get_application_note,
)
from app.api.routes.legacy.document_set import DocumentSet, get_document_set
from app.api.routes.legacy.orm_ops import (
    check_access,
    get_codebase_by_id,
)
from app.api.routes.legacy.scalars import ID, NodeType
from app.api.routes.legacy.tree import FlatNode, get_codebase_tree
from app.repositories.github_app_installations_repository import (
    GithubAppInstallationsRepository,
)
from app.utils.gh_ops import fetch_repos
from database.models_v1 import Workspace
from graphql import GraphQLError
from sqlmodel import select
from strawberry.types import Info
from strawberry.types.nodes import Selection

logger = logging.getLogger(__name__)


@strawberry.type
class MeResponse:
    id: ID


def is_code_content_requested(info: Info) -> bool:
    """Recursively check if 'content' field under 'code' is requested in the query."""

    def has_content_field(fields: list[Selection]) -> bool:
        for field in fields:
            if field.name == "code" and any(
                subfield.name == "content" for subfield in field.selections
            ):
                return True
            # Recursively check nested fields in case of deeply nested selections
            if field.selections and has_content_field(field.selections):
                return True
        return False

    return has_content_field(info.selected_fields)


@strawberry.type
class Query:
    @strawberry.field
    def organization(self, info: Info, id: str) -> OrganizationResult:
        session = info.context.session
        if info.context.user.organization_id != id:
            raise GraphQLError(
                "Organization not found", extensions={"code": "NOT_FOUND"}
            )

        workspaces = session.exec(
            select(Workspace).where(
                Workspace.organization_id == info.context.user.organization_id
            )
        ).all()

        return OrganizationResult(
            id=info.context.user.organization_id,
            name=info.context.user.organization_display_name,
            display_name=info.context.user.organization_display_name,
            workspaces=list(workspaces),
        )

    @strawberry.field
    def codebase(self, info: Info, id: ID | None = None) -> CodebaseResults:
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
    def documentSet(
        self,
        info: Info,
        nodeKind: NodeType,
        path: str | None = None,
        workspaceId: ID | None = None,
        codebaseId: ID | None = None,
        versionId: ID | None = None,
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
            primary_asset_id=str(codebaseId),
        ):
            raise GraphQLError("Access denied", extensions={"code": "NOT_FOUND"})

        fetch_code_content = is_code_content_requested(info)
        logger.info("Is code content requested: %s", fetch_code_content)
        return get_document_set(
            nodeKind,
            path,
            str(workspaceId),
            str(codebaseId),
            info.context.user.organization_id,
            session,
            fetch_code_content,
            versionId,
        )

    @strawberry.field
    def applicationNote(
        self, info: Info, id: ID | None = None
    ) -> ApplicationNoteResponse:
        session = info.context.session
        if id is not None:
            id_str = str(id)
        else:
            raise GraphQLError(
                "id must not be None", extensions={"code": "BAD_REQUEST"}
            )
        organization_id = info.context.user.organization_id
        derived_content_id = id_str
        if not check_access(
            session, organization_id, derived_content_id=derived_content_id
        ):
            raise GraphQLError("Access denied", extensions={"code": "NOT_FOUND"})
        return get_application_note(id_str, session, info.context.user.organization_id)

    @strawberry.field
    def tree(
        self,
        info: Info,
        codebaseId: ID | None = None,
        workspaceId: ID | None = None,
        versionId: ID | None = None,
    ) -> list[FlatNode]:
        session = info.context.session
        user = info.context.user
        # Access now happens on Primary Asset
        # if not check_access(session, user.organization_id, primary_asset_id=str(codebaseId), version_id=str(versionId) if versionId else None):
        #     raise GraphQLError("Access denied", extensions={"code": "NOT_FOUND"})

        return get_codebase_tree(
            session=session,
            organization_id=user.organization_id,
            version_id=str(versionId) if versionId else None,
        )

    # @strawberry.field
    # def symbolSet(
    #     self, info: Info, sourceContentId: ID, page: int = 1, pageSize: int = 10
    # ) -> SymbolSetResponse:
    #     session = info.context.session
    #     organization_id = info.context.user.organization_id
    #     if not check_access(
    #         session, organization_id, source_content_id=str(sourceContentId)
    #     ):
    #         raise GraphQLError("Access denied", extensions={"code": "NOT_FOUND"})
    #     return symbol_set(
    #         session, str(sourceContentId), organization_id, page, pageSize
    #     )

    @strawberry.mutation
    def applicationNoteEdit(self, call_id: ID) -> ApplicationNoteEditResponse:
        # Assuming access check is performed within the application_note_edit function or not required due to the nature of the mutation.
        return application_note_edit(str(call_id))

    @strawberry.field
    def me(self, info: Info) -> MeResponse:
        user = info.context.user
        return MeResponse(id=user.subject)  # type: ignore

    @strawberry.field
    def connectedGitProviders(self, info: Info) -> list[GitProvider]:
        """This endpoint lists which git providers (ie Github, Gitlab, etc)that a user/org has configured. It is polled by the UI."""
        providers = []
        user = info.context.user
        gh_repository = GithubAppInstallationsRepository(info.context.session)
        if len(gh_repository.list_by_organization_id(user.organization_id)) > 0:
            providers.append(
                GitProvider(
                    display_name="GitHub",
                    name="github",
                    logo_url="https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png",
                )
            )
        return providers

    @strawberry.field
    def reposByGitProvider(self, info: Info, provider: str) -> list[GitRepository]:
        repos = []
        user = info.context.user
        session = info.context.session

        if provider != "github":
            raise NotImplementedError()

        git_repos = fetch_repos(session, user.organization_id)
        repos = [
            GitRepository(
                provider_name=provider,
                repo_name=repo["name"],
                org=repo["owner"]["login"],
                last_updated=datetime.fromisoformat(repo["updated_at"]),
                metadata=repo,
            )
            for repo in git_repos
        ]
        # Assuming the response from fetch_repos is a list of dictionaries
        return repos
