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


def get_source_content_by_id(
    session: Session, id: str, org_id: str
) -> SourceContent | None:
    statement = (
        select(SourceContent)
        .where(SourceContent.id == id)
        .join(Codebase)
        .join(Workspace)
        .where(Workspace.organization_id == org_id)
    )
    result = session.exec(statement)
    return result.first()


def get_derived_content_by_id(
    session: Session, id: str, org_id: str
) -> DerivedContent | None:
    statement = (
        select(DerivedContent)
        .where(DerivedContent.id == id)
        .join(SourceContent)
        .join(Codebase)
        .join(Workspace)
        .where(Workspace.organization_id == org_id)
    )
    result = session.exec(statement)
    return result.first()


def get_derived_content_by_id_no_org_check(
    session: Session, id: str
) -> DerivedContent | None:
    statement = (
        select(DerivedContent)
        .where(DerivedContent.id == id)
        .join(SourceContent)
        .join(Codebase)
        .join(Workspace)
    )
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
    codebase_id: str, organization_id: str, session: Session
) -> list[SupplementalContent]:
    logger.info(f"Fetching supplemental content for codebase {codebase_id}")
    supplement_contents = []
    source_contents = session.exec(
        select(SourceContent)
        .where(SourceContent.codebase_id == codebase_id)
        .join(SourceContentType)
        .where(SourceContentType.type_name == "SUPPLEMENTAL_DOCUMENT")
        .join(Workspace)
        .where(Workspace.organization_id == organization_id)
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
