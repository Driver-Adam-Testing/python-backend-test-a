import enum

from sqlmodel.ext.asyncio.session import AsyncSession
import uuid
from database.models_v1 import (
    Codebase,
    DerivedContentType,
    DerivedContent,
)
from pathlib import Path
from uuid import UUID


async def get_codebase_by_id(codebase_id: uuid.UUID) -> Codebase:
    from database.db import async_engine
    from sqlmodel import select

    async with AsyncSession(async_engine) as session:
        statement = select(Codebase).where(Codebase.id == codebase_id)
        return (await session.exec(statement)).one()


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


# TODO this actually would get source and derived content if the incoming types weren't correct
async def get_source_contents_by_codebase_id(
    codebase_id: uuid.UUID, content_types: set[SourceContentTypeMap]
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
                DerivedContent.codebase_id == codebase_id,
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
        ):
            res_list.append(res)
        elif res.content_type_id != file_content_type_id:
            res_list.append(res)

    return res_list


def download_source_content_file(
    s3_client: any,
    codebase_storage_url: str,
    codebase_root: str,
    source_content_rel_path: str,
    download_root: Path,
) -> Path:
    parsed_url = codebase_storage_url.replace("https://", "").split("/")
    bucket_name = parsed_url[0].split(".")[
        0
    ]  # Extract the bucket name from the URL... fragile
    s3_key = "/".join(parsed_url[1:]) + f"/source/{source_content_rel_path}"
    local_download_path = download_root / source_content_rel_path
    local_download_path.parent.mkdir(parents=True, exist_ok=True)

    print("Bucket name:", bucket_name)
    print("S3 key:", s3_key)
    print("Local download path:", local_download_path)
    s3_client.download_file(bucket_name, s3_key, str(local_download_path))
    print(f"File downloaded to {local_download_path}")
    return local_download_path
