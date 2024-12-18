import enum
import uuid
from pathlib import Path
from uuid import UUID

from database.models_v1 import (
    Codebase,
    DerivedContent,
    DerivedContentType,
    InspectionVersion,
    InspectorRun,
    Workspace,
)
from sqlmodel.ext.asyncio.session import AsyncSession


async def get_codebase_by_id(codebase_id: uuid.UUID) -> Codebase:
    from database.db import async_engine
    from sqlmodel import select

    async with AsyncSession(async_engine) as session:
        statement = select(Codebase).where(Codebase.id == codebase_id)
        return (await session.exec(statement)).one()


async def get_version_by_id(version_id: uuid.UUID) -> InspectionVersion:
    from database.db import async_engine
    from sqlmodel import select

    async with AsyncSession(async_engine) as session:
        statement = select(InspectionVersion).where(InspectionVersion.id == version_id)
        return (await session.exec(statement)).one()


async def get_workspace_by_id(workspace_id: uuid.UUID) -> Workspace:
    from database.db import async_engine
    from sqlmodel import select

    async with AsyncSession(async_engine) as session:
        statement = select(Workspace).where(Workspace.id == workspace_id)
        return (await session.exec(statement)).one()


async def create_inspector_run(version_id: uuid.UUID) -> uuid.UUID:
    from database.db import async_engine

    async with AsyncSession(async_engine) as session:
        inspector_run = InspectorRun(inspection_version_id=version_id)
        session.add(inspector_run)
        await session.commit()
        await session.refresh(inspector_run)
        run_id = inspector_run.id

    return run_id


class SourceContentTypeMap(enum.Enum):
    # This is because these are in a separate table and arent already defined in the db package
    # Hacky... would be better to have concrete enum in db package
    FILE = "codebase-file"
    DIRECTORY = "codebase-directory"
    CODEBASE_ROOT = "codebase"


class DerivedContentTypeMap(enum.Enum):
    # This is because these are in a separate table and arent already defined in the db package
    # Hacky... would be better to have concrete enum in db package
    SYMBOL = "symbol"
    SHORT_PARAGRAPH_DESCRIPTION = "short_paragraph_description"
    TERSE_SENTENCE_DESCRIPTION = "terse_sentence_description"
    LONG_DESCRIPTION = "long_description"
    QUICK_START_ENTRY = "quick_start_entry"
    QUICK_START_GETTING_STARTED = "quick_start_getting_started"
    QUICK_START_DEPENDENCIES = "quick_start_dependencies"
    QUICK_START_USE = "quick_start_use"
    ARCHITECTURE_DIAGRAM = "architecture_diagram"
    CHUNK_DESCRIPTIONS = "chunk_descriptions"
    APPLICATION_NOTE = "application_note"
    SHORT_SENTENCE_DESCRIPTION = "short_sentence_description"


async def get_derived_content_type_uuid(content_type: DerivedContentTypeMap) -> UUID:
    from database.db import async_engine
    from sqlmodel import select

    dct_uuid = None
    async with AsyncSession(async_engine) as session:
        sel_statement = select(DerivedContentType).where(
            DerivedContentType.type_name == content_type.value
        )
        res_dct = (await session.exec(sel_statement)).first()
        if res_dct:
            dct_uuid = res_dct.id
    return dct_uuid


# TODO remove the need for this...
async def get_rel_path_workspace_id_codebase_id_from_source_content_id(
    source_content_id: UUID,
) -> tuple[str, str, str]:
    from database.db import async_engine
    from sqlmodel import select

    async with AsyncSession(async_engine) as session:
        statement = select(DerivedContent).where(DerivedContent.id == source_content_id)
        res = (await session.exec(statement)).first()
        return (res.relative_path, res.workspace_id, res.codebase_id)


async def get_source_content_type_uuid(content_type: SourceContentTypeMap) -> UUID:
    from database.db import async_engine
    from sqlmodel import select

    sct_uuid = None
    async with AsyncSession(async_engine) as session:
        sel_statement = select(DerivedContentType).where(
            DerivedContentType.type_name == content_type.value
        )
        res_sct = (await session.exec(sel_statement)).first()
        if res_sct:
            sct_uuid = res_sct.id
    return sct_uuid


async def get_latest_run_from_version_id(version_id: uuid.UUID) -> uuid.UUID | None:
    from database.db import async_engine
    from sqlmodel import select

    async with AsyncSession(async_engine) as session:
        statement = (
            select(InspectorRun)
            .where(InspectorRun.inspection_version_id == version_id)
            .order_by(InspectorRun.created_at.desc())
        )
        result = (await session.exec(statement)).first()
        # It is possible, though uncommon, that a version won't have a run
        # This happens, for example, for codebases that were created before runs/versions were introduced, but versions
        # were created during a migration for those codebases
        if result is None:
            return None
        return result.id


# TODO this actually would get source and derived content if the incoming types weren't correct
async def get_analyzable_source_contents_by_version_id(
    version_id: uuid.UUID, content_types: set[SourceContentTypeMap]
) -> list[DerivedContent]:
    from database.db import async_engine
    from sqlmodel import select

    # TODO: Implement the appropriate way to filter source content nodes
    # down to what has been configured.
    async with AsyncSession(async_engine) as session:
        statement = (
            select(DerivedContent)
            .join(
                DerivedContentType,
                DerivedContent.content_type_id == DerivedContentType.id,
            )
            .where(
                DerivedContentType.type_name.in_([ct.value for ct in content_types]),
                DerivedContent.version_id == version_id,
                # SourceContent.misc_metadata.op("->>")("is_analyzable") == 'true'
            )
        )
        results = await session.exec(statement)

    file_content_type_id = await get_source_content_type_uuid(SourceContentTypeMap.FILE)

    res_list = []
    for res in results.all():
        if (
            res.content_type_id == file_content_type_id
            and res.misc_metadata["is_analyzable"] is True
        ) or res.content_type_id != file_content_type_id:
            res_list.append(res)

    return res_list


# TODO may need to change
def download_source_content_file(
    s3_client: any,
    bucket_name: str,
    codebase_id: str,
    version_id: str,
    source_content_rel_path: str,
    download_root: Path,
) -> Path:
    s3_key = f"{codebase_id}/version/{version_id}/source/{source_content_rel_path}"
    local_download_path = download_root / source_content_rel_path
    local_download_path.parent.mkdir(parents=True, exist_ok=True)

    s3_client.download_file(bucket_name, s3_key, str(local_download_path))
    return local_download_path
