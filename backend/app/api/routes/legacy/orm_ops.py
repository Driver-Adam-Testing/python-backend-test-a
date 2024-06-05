import os

from database.models_v1 import (
    Codebase,
    DerivedContent,
    SourceContent,
    SourceContentType,
    Workspace,
)
from sqlmodel import Session, delete, select

from app.api.routes.legacy.api_types import SupplementalContent
from app.api.routes.legacy.s3 import S3BucketAccess
from app.api.routes.legacy.scalars import ID
from app.core.logger import logger


def get_workspace_related_entities(session: Session, org_id: str) -> list[Workspace]:
    statement = (
        select(Workspace)
        .join(Codebase, Workspace.id == Codebase.workspace_id)  # type: ignore
        .where(Workspace.organization_id == org_id)
    )
    result = session.exec(statement).all()
    return result  # type: ignore


def get_source_content_by_id(session: Session, id: str) -> SourceContent | None:
    statement = select(SourceContent).where(SourceContent.id == id)
    result = session.exec(statement)
    return result.first()


def get_derived_content_by_id(session: Session, id: str) -> DerivedContent | None:
    statement = select(DerivedContent).where(DerivedContent.id == id)
    result = session.exec(statement)
    return result.first()


def delete_codebase_by_id(session: Session, codebase_id: str) -> bool:
    with session.begin():
        # Fetch the IDs of SourceContent related to the codebase
        source_content_ids = session.exec(
            select(SourceContent.id).where(SourceContent.codebase_id == codebase_id)
        )
        source_content_ids = source_content_ids.scalars().all()  # type: ignore

        # Delete DerivedContent associated with the fetched SourceContent IDs
        if source_content_ids:
            session.exec(
                delete(DerivedContent).where(
                    DerivedContent.source_content_id.in_(source_content_ids)  # type: ignore
                )
            )

        # Delete all associated SourceContent
        session.exec(
            delete(SourceContent).where(SourceContent.codebase_id == codebase_id)  # type: ignore
        )

        # Finally, delete the codebase itself
        count = session.exec(delete(Codebase).where(Codebase.id == codebase_id))  # type: ignore
        return count > 0


def get_codebase_by_id(session: Session, codebase_id: str) -> Codebase | None:
    statement = select(Codebase).where(Codebase.id == codebase_id)
    result = session.exec(statement)
    return result.first()


def supplemental_content_by_codebase_id(
    session: Session, codebase_id: str
) -> list[SupplementalContent]:
    logger.info(f"Fetching supplemental content for codebase {codebase_id}")
    supplement_contents = []
    source_contents = session.exec(
        select(SourceContent)
        .where(SourceContent.codebase_id == codebase_id)
        .join(SourceContentType)
        .where(SourceContentType.type_name == "SUPPLEMENTAL_DOCUMENT")
    ).all()

    if source_contents:
        logger.info(
            f"Found {len(source_contents)} supplemental content for codebase {codebase_id}"
        )

        for source_content in source_contents:
            s3_access = S3BucketAccess(
                organization_id=source_content.workspace.organization_id,
                codebase_id=str(codebase_id),
            )
            s3_access.get_file_path(source_content.relative_path)
            download_url = s3_access.get_signed_upload_url(
                relative_path=source_content.relative_path, expiration=3600
            )
            supplement_content = SupplementalContent(
                id=ID(source_content.id),
                name=os.path.basename(source_content.relative_path),
                relative_path=source_content.relative_path,
                download_url=download_url,
                created_at=source_content.created_at.isoformat(),
            )
            supplement_contents.append(supplement_content)
    else:
        logger.info(f"No supplemental content found for codebase {codebase_id}")

    return supplement_contents


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
        source_content = session.exec(
            select(SourceContent).where(SourceContent.id == source_content_id)
        ).first()
        access_checks.append(
            source_content
            and source_content.codebase.workspace.organization_id == organization_id
        )

    if derived_content_id:
        derived_content = session.exec(
            select(DerivedContent).where(DerivedContent.id == derived_content_id)
        ).first()
        access_checks.append(
            derived_content
            and derived_content.source_content.codebase.workspace.organization_id
            == organization_id
        )

    return all(access_checks)
