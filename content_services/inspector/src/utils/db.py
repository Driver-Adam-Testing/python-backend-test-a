import uuid
from pathlib import Path

from database.models_v1 import (
    DerivedContent,
    InspectorRun,
)
from database.models_v2 import Node, Version
from database.models_v2_enums import ContentKind, NodeKind
from sqlmodel.ext.asyncio.session import AsyncSession


async def get_version_by_id(version_id: uuid.UUID) -> Version:
    from database.db import async_engine
    from sqlalchemy.orm import selectinload
    from sqlmodel import select

    async with AsyncSession(async_engine) as session:
        statement = (
            select(Version)
            .where(Version.id == version_id)
            .options(selectinload(Version.primary_asset))
        )
        return (await session.exec(statement)).one()


async def try_get_prev_version(version_id: uuid.UUID) -> None | Version:
    from database.db import async_engine
    from sqlmodel import select

    async with AsyncSession(async_engine) as session:
        stmt = select(Version).where(Version.id == version_id)
        version = (await session.exec(stmt)).one()
        stmt = select(Version).where(Version.id == version.previous_version_id)
        previous_version = (await session.exec(stmt)).first()
        return previous_version


async def create_inspector_run(version_id: uuid.UUID) -> uuid.UUID:
    from database.db import async_engine

    async with AsyncSession(async_engine) as session:
        inspector_run = InspectorRun(
            inspection_version_id=None,
            version_id=version_id,
        )
        session.add(inspector_run)
        await session.commit()
        await session.refresh(inspector_run)
        run_id = inspector_run.id

    return run_id


async def try_get_latest_run_from_version_id(version_id: uuid.UUID) -> uuid.UUID | None:
    from database.db import async_engine
    from sqlmodel import select

    async with AsyncSession(async_engine) as session:
        statement = (
            select(InspectorRun)
            .where(
                InspectorRun.inspection_version_id == version_id
            )  # TODO this fk name will probably be version_id once updated
            .order_by(InspectorRun.created_at.desc())
        )
        result = (await session.exec(statement)).first()
        # It is possible, though uncommon, that a version won't have a run
        # This happens, for example, for codebases that were created before runs/versions were introduced, but versions
        # were created during a migration for those codebases
        if result is None:
            return None
        return result.id


# TODO : get analyable nodes by version_id
async def get_analyzable_nodes_by_version_id(
    version_id: uuid.UUID, content_types: set[NodeKind]
) -> list[Node]:
    from database.db import async_engine
    from sqlmodel import select

    async with AsyncSession(async_engine) as session:
        statement = select(Node).where(
            Node.version_id == version_id,
            Node.kind.in_(content_types),
        )

        results = await session.exec(statement)

    res_list = []
    for res in results.all():
        is_file = res.kind == NodeKind.CODEBASE_FILE
        is_directory = res.kind == NodeKind.CODEBASE_DIRECTORY
        is_analyzable_file = is_file and res.misc_metadata["is_analyzable"] is True
        if is_directory or is_analyzable_file:
            res_list.append(res)
    return res_list


async def get_source_code_derived_content(node_id: uuid.UUID) -> DerivedContent:
    from database.db import async_engine
    from sqlmodel import select

    async with AsyncSession(async_engine) as session:
        statement = select(DerivedContent).where(
            DerivedContent.node_id == node_id,
            DerivedContent.content_kind == ContentKind.CODEBASE_FILE,
        )
        return (await session.exec(statement)).one()


# TODO may need to change
def download_source_file(
    s3_client: any,
    bucket_name: str,
    primary_asset_id: str,
    version_id: str,
    node_rel_path: str,
    download_root: Path,
) -> Path:
    s3_key = f"{primary_asset_id}/{version_id}/{node_rel_path}"
    local_download_path = download_root / node_rel_path
    local_download_path.parent.mkdir(parents=True, exist_ok=True)

    s3_client.download_file(bucket_name, s3_key, str(local_download_path))
    return local_download_path
