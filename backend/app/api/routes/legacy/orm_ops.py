from database.models_v1 import (
    Codebase,
    DerivedContent,
    Workspace,
)
from sqlmodel import Session, delete, select


def get_workspace_related_entities(session: Session, org_id: str) -> list[Workspace]:
    statement = (
        select(Workspace)
        .join(Codebase, Workspace.id == Codebase.workspace_id)  # type: ignore # noqa: PGH003
        .where(Workspace.organization_id == org_id)
    )
    result = session.exec(statement).all()
    return result  # type: ignore # noqa: PGH003


# TODO remove me
def get_source_content_by_id(session: Session, id: str) -> DerivedContent | None:
    statement = select(DerivedContent).where(DerivedContent.id == id)
    result = session.exec(statement)
    return result.first()


def get_derived_content_by_id(session: Session, id: str) -> DerivedContent | None:
    statement = select(DerivedContent).where(DerivedContent.id == id)
    result = session.exec(statement)
    return result.first()


def delete_codebase_by_id(session: Session, codebase_id: str) -> bool:
    # TODO cascade delete from codebase to content
    with session.begin():
        # Delete all associated SourceContent
        session.exec(
            delete(DerivedContent).where(DerivedContent.codebase_id == codebase_id)  # type: ignore  # noqa: PGH003
        )
        # Finally, delete the codebase itself
        count = session.exec(delete(Codebase).where(Codebase.id == codebase_id))  # type: ignore # noqa: PGH003
        return count > 0


def get_codebase_by_id(session: Session, codebase_id: str) -> Codebase | None:
    statement = select(Codebase).where(Codebase.id == codebase_id)
    result = session.exec(statement)
    return result.first()


def check_access(
    session: Session,
    organization_id: str,
    workspace_id: str | None = None,
    codebase_id: str | None = None,
    source_content_id: str | None = None,
    derived_content_id: str | None = None,
) -> bool:
    access_checks = []

    if workspace_id:
        workspace = session.exec(
            select(Workspace).where(Workspace.id == workspace_id)
        ).first()
        access_checks.append(workspace and workspace.organization_id == organization_id)

    if codebase_id:
        codebase = session.exec(
            select(Codebase).where(Codebase.id == codebase_id)
        ).first()
        access_checks.append(
            codebase and codebase.workspace.organization_id == organization_id
        )

    if source_content_id:
        content = session.exec(
            select(DerivedContent).where(DerivedContent.id == source_content_id)
        ).first()
        access_checks.append(
            content and content.codebase.workspace.organization_id == organization_id
        )

    if derived_content_id:
        derived_content = session.exec(
            select(DerivedContent).where(DerivedContent.id == derived_content_id)
        ).first()
        access_checks.append(
            derived_content
            and derived_content.workspace.organization_id == organization_id
        )

    return all(access_checks)
