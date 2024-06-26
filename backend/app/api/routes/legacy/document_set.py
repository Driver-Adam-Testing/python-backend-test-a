import json
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

import strawberry
from database.models_v1 import (
    SourceContent,
    SourceContentType, DerivedContentType, DerivedContent,
)
from fastapi import HTTPException
from sqlmodel import Session, select

from app.api.routes.legacy.s3 import S3BucketAccess

# from app.api.routes.legacy.utils import source_type_id_map, derive_bucket_name, download_source_content
from app.core.logger import logger


class DerivedContentTypes(Enum):
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


@strawberry.type
class Document:
    id: UUID = UUID(int=0)
    content: str = ""


@strawberry.type
class Short:
    terse_sentence: str = ""
    single_sentence: str = ""
    single_paragraph: str = ""
    terse_sentence_document: Document | None = None
    single_sentence_document: Document | None = None
    single_paragraph_document: Document | None = None


@strawberry.type
class Quickstart:
    use: str = ""
    dependencies: str = ""
    entry: str = ""
    getting_started: str = ""
    use_document: Document | None = None
    dependencies_document: Document | None = None
    entry_document: Document | None = None
    getting_started_document: Document | None = None


@strawberry.type
class Code:
    file_name: str = ""
    extension: str = ""
    content: str = ""


@strawberry.type
class ApplicationNote:
    id: str = ""
    status: str = ""
    prompt: str = ""
    name: str = ""
    content: str = ""
    description: str = ""
    metadata: str = ""
    generation_timestamp: datetime | None = None


@strawberry.type
class DocumentSet:
    source_content_id: str = strawberry.field(default="")
    architecture: str = strawberry.field(default="")
    architecture_document: Document = strawberry.field(default_factory=Document)
    long: str = strawberry.field(default="")
    long_document: Document = strawberry.field(default_factory=Document)
    short: Short = strawberry.field(default_factory=Short)
    quickstart: Quickstart = strawberry.field(default_factory=Quickstart)
    chunk_descriptions: list[str] | None = strawberry.field(default=None)
    code: Code = strawberry.field(default_factory=Code)
    application_notes: list[ApplicationNote] | None = strawberry.field(default_factory=lambda: [])


# TODO: Get rid of this!
def node_kind_map(node_kind: str) -> str:
    if node_kind == "resource":
        return "codebase"
    elif node_kind == "directory":
        return "codebase-directory"
    elif node_kind == "file":
        return "codebase-file"
    else:
        raise ValueError(f"Invalid node kind: {node_kind}")


def source_content_types_map(db: Session) -> dict[str, str]:
    types = db.exec(select(SourceContentType)).all()
    return {type.type_name: str(type.id) for type in types}


def source_type_id_map(kind: str, db: Session) -> dict[str, Any]:
    derive_types = source_content_types_map(db)
    kind_translation = node_kind_map(kind)
    return {"typeName": kind_translation, "id": derive_types[kind_translation]}


def get_document_set(
        node_kind: str,
        path: str,
        workspace_id: str,
        codebase_id: str,
        organization_id: str,
        session: Session,
) -> DocumentSet:
    relative_path = path
    source_content_type = source_type_id_map(node_kind, session)

    if source_content_type["typeName"] == "codebase":
        relative_path = path.replace("/", "")

    query = select(SourceContent).where(
        SourceContent.relative_path == relative_path,
        SourceContent.source_content_type_id == source_content_type["id"],
    )

    if workspace_id:
        query = query.where(SourceContent.workspace_id == workspace_id)
    if codebase_id:
        query = query.where(SourceContent.codebase_id == codebase_id)
    content = session.exec(query).first()

    if content is None:
        raise HTTPException(status_code=400, detail="No content found")

    dc_query = (
        select(DerivedContent)
        .join(DerivedContentType, DerivedContent.derived_content_type_id == DerivedContentType.id)
        .where(
            DerivedContent.source_content_id == content.id,
            DerivedContentType.type_name != DerivedContentTypes.SYMBOL.value,  # Updated line
        ))
    docs = session.exec(dc_query).all()

    document_set = DocumentSet(source_content_id=str(content.id))  # type: ignore
    for doc in docs:
        derived_content_type = doc.derived_content_type.type_name
        if doc.id is None:
            continue
        if doc.content is None:
            doc.content = ""
        if derived_content_type == DerivedContentTypes.SYMBOL.value:
            continue
        if derived_content_type == DerivedContentTypes.LONG_DESCRIPTION.value:
            document_set.long = doc.content
            document_set.long_document = Document(id=doc.id, content=doc.content)  # type: ignore
        elif (
                derived_content_type
                == DerivedContentTypes.SHORT_PARAGRAPH_DESCRIPTION.value
        ):
            document_set.short.single_paragraph = doc.content
            document_set.short.single_paragraph_document = Document(
                id=doc.id,
                content=doc.content,  # type: ignore
            )
        elif (
                derived_content_type == DerivedContentTypes.SHORT_SENTENCE_DESCRIPTION.value
        ):
            document_set.short.single_sentence = doc.content
            document_set.short.single_sentence_document = Document(
                id=doc.id,
                content=doc.content,  # type: ignore
            )
        elif (
                derived_content_type == DerivedContentTypes.TERSE_SENTENCE_DESCRIPTION.value
        ):
            document_set.short.terse_sentence = doc.content
            document_set.short.terse_sentence_document = Document(
                id=doc.id,
                content=doc.content,  # type: ignore
            )
        elif derived_content_type == DerivedContentTypes.ARCHITECTURE_DIAGRAM.value:
            document_set.architecture = doc.content
            document_set.architecture_document = Document(
                id=doc.id,
                content=doc.content,  # type: ignore
            )
        elif derived_content_type == DerivedContentTypes.CHUNK_DESCRIPTIONS.value:
            if document_set.chunk_descriptions is None:
                document_set.chunk_descriptions = []
            document_set.chunk_descriptions.extend(doc.content.split("\n\n\n"))
        elif (
                derived_content_type
                == DerivedContentTypes.QUICK_START_GETTING_STARTED.value
        ):
            document_set.quickstart.getting_started = doc.content
            document_set.quickstart.getting_started_document = Document(
                id=doc.id,
                content=doc.content,  # type: ignore
            )
        elif derived_content_type == DerivedContentTypes.QUICK_START_DEPENDENCIES.value:
            document_set.quickstart.dependencies = doc.content
            document_set.quickstart.dependencies_document = Document(
                id=doc.id,
                content=doc.content,  # type: ignore
            )
        elif derived_content_type == DerivedContentTypes.QUICK_START_ENTRY.value:
            document_set.quickstart.entry = doc.content
            document_set.quickstart.entry_document = Document(
                id=doc.id,  # type: ignore
                content=doc.content,  # type: ignore
            )
        elif derived_content_type == DerivedContentTypes.QUICK_START_USE.value:
            document_set.quickstart.use = doc.content  # type: ignore
            document_set.quickstart.use_document = Document(
                id=doc.id,  # type: ignore
                content=doc.content,  # type: ignore
            )
        elif derived_content_type == DerivedContentTypes.APPLICATION_NOTE.value:
            try:
                parsed_content = json.loads(doc.content)  # type: ignore
                if document_set.application_notes is None:
                    document_set.application_notes = []
                document_set.application_notes.append(
                    ApplicationNote(
                        id=doc.id,  # type: ignore
                        status=doc.status,
                        prompt=parsed_content.get("description", ""),
                        name=parsed_content.get("name", ""),
                        content=parsed_content.get("content", ""),
                        description=parsed_content.get("description", ""),
                        metadata=doc.metadata,  # type: ignore
                        generation_timestamp=doc.created_at,
                    )
                )
            except json.JSONDecodeError as e:
                logger.warning(f"[ParseError]: {doc.id} - {str(e)}")
        else:
            logger.warning(
                f"no DerivedContentTypes documentSet match for {derived_content_type}"
            )
    if source_content_type["typeName"] == "codebase-file":
        s3_access = S3BucketAccess(
            organization_id=organization_id,
            codebase_id=codebase_id if codebase_id else str(content.codebase_id),
        )
        code_content = s3_access.get_file_content(relative_path=content.relative_path)
        document_set.code = Code(  # type: ignore
            file_name=content.relative_path.split("/")[-1],
            extension=content.relative_path.split(".")[-1],
            content=code_content,
        )

    return document_set
