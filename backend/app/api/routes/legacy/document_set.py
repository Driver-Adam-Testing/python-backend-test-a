import json
from datetime import datetime
from enum import Enum
from uuid import UUID

import strawberry
from app.api.routes.legacy.s3 import S3BucketAccess
from app.core.logger import logger
from database.models_v1 import DerivedContent
from database.models_v2 import (
    Node,
    PrimaryAsset,
    Version,
)
from database.models_v2_enums import ContentKind, NodeKind
from fastapi import HTTPException
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select


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
class CodeMetadata:
    size: int | None
    sloc: int | None
    extension: str | None
    is_binary: bool | None
    is_hex: bool | None
    is_analyzable: bool = True
    is_blacklisted: bool = False


@strawberry.type
class Code:
    file_name: str = ""
    extension: str = ""
    content: str = ""
    metadata: CodeMetadata | None = None


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
class TopLevel:
    short_sentence: str = ""
    short_paragraph: str = ""
    terse_sentence: str = ""
    long_description: str = ""
    short_sentence_document: Document | None = None
    short_paragraph_document: Document | None = None
    terse_sentence_document: Document | None = None
    long_description_document: Document | None = None


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
    toplevel: TopLevel = strawberry.field(default_factory=TopLevel)
    application_notes: list[ApplicationNote] | None = strawberry.field(
        default_factory=list
    )


def node_kind_map(node_kind: str) -> str:
    if node_kind == "resource":
        return "codebase"
    elif node_kind == "directory":
        return "codebase-directory"
    elif node_kind == "file":
        return "codebase-file"
    else:
        raise ValueError(f"Invalid node kind: {node_kind}")


def fetch_code_metadata(node: Node) -> CodeMetadata | None:
    if not node.misc_metadata:
        return None
    return CodeMetadata(
        size=node.misc_metadata.get("size"),
        sloc=node.misc_metadata.get("sloc"),
        extension=node.misc_metadata.get("extension"),
        is_binary=node.misc_metadata.get("is_binary"),
        is_hex=node.misc_metadata.get("is_hex"),
        is_analyzable=node.misc_metadata.get("is_analyzable"),
        is_blacklisted=node.misc_metadata.get("is_blacklisted"),
    )


def fetch_code_content_from_s3(node: Node) -> str:
    s3_access = S3BucketAccess(
        organization_id=node.version.primary_asset.organization_id,
        primary_asset_id=node.version.primary_asset_id,
        version_id=node.version_id,
    )
    return s3_access.get_file_content(relative_path=node.relative_path)


def get_document_set(
    node_kind: str,
    path: str,
    primary_asset_id: str,
    organization_id: str,
    session: Session,
    fetch_code_content: bool,
    version_id: str | None = None,
) -> DocumentSet:
    # Find the primary asset
    primary_asset = session.get(PrimaryAsset, primary_asset_id)
    if not primary_asset or primary_asset.organization_id != organization_id:
        raise HTTPException(
            status_code=404, detail="Primary asset not found or not in org"
        )

    if primary_asset.kind not in ["CODEBASE", "FILE", "PAGE"]:
        raise HTTPException(
            status_code=400, detail="Primary asset type does not match node kind"
        )

    relative_path = path

    # Determine the VersionRow
    if version_id:
        version = session.get(Version, version_id)
        if not version or version.primary_asset_id != primary_asset.id:
            raise ValueError(
                f"Version with id {version_id} not found or not tied to this asset"
            )
    else:
        # No version_id provided, get the latest version
        version = session.exec(
            select(Version)
            .where(Version.primary_asset_id == primary_asset.id)
            .order_by(Version.created_at.desc())
        ).first()

    if not version:
        raise HTTPException(status_code=400, detail="No version found")

    # Find the node
    node = session.exec(
        select(Node)
        .where(Node.version_id == version.id, Node.relative_path == relative_path)
        .options(selectinload(Node.version).selectinload(Version.primary_asset))
    ).one_or_none()

    if not node:
        raise HTTPException(status_code=400, detail="No node found for given path")

    docs = session.exec(
        select(DerivedContent).where(DerivedContent.node_id == node.id)
    ).all()

    document_set = DocumentSet(source_content_id=str(node.id))  # type: ignore

    for doc in docs:
        # Identify doc type by doc.content_kind
        doc_type = doc.content_kind
        if doc.id is None:
            continue
        if doc.content is None:
            doc.content = ""

        # Skip symbols
        if doc_type == ContentKind.SYMBOL.value:
            continue

        if doc_type == ContentKind.LONG_DESCRIPTION.value:
            document_set.long = doc.content
            document_set.long_document = Document(id=doc.id, content=doc.content)
        elif doc_type == ContentKind.SHORT_PARAGRAPH_DESCRIPTION.value:
            document_set.short.single_paragraph = doc.content
            document_set.short.single_paragraph_document = Document(
                id=doc.id, content=doc.content
            )
        elif doc_type == ContentKind.SHORT_SENTENCE_DESCRIPTION.value:
            document_set.short.single_sentence = doc.content
            document_set.short.single_sentence_document = Document(
                id=doc.id, content=doc.content
            )
        elif doc_type == ContentKind.TERSE_SENTENCE_DESCRIPTION.value:
            document_set.short.terse_sentence = doc.content
            document_set.short.terse_sentence_document = Document(
                id=doc.id, content=doc.content
            )
        elif doc_type == ContentKind.ARCHITECTURE_DIAGRAM.value:
            document_set.architecture = doc.content
            document_set.architecture_document = Document(
                id=doc.id, content=doc.content
            )
        elif doc_type == ContentKind.CHUNK_DESCRIPTIONS.value:
            if document_set.chunk_descriptions is None:
                document_set.chunk_descriptions = []
            document_set.chunk_descriptions.extend(doc.content.split("\n\n\n"))
        elif doc_type == ContentKind.QUICK_START_GETTING_STARTED.value:
            document_set.quickstart.getting_started = doc.content
            document_set.quickstart.getting_started_document = Document(
                id=doc.id, content=doc.content
            )
        elif doc_type == ContentKind.QUICK_START_DEPENDENCIES.value:
            document_set.quickstart.dependencies = doc.content
            document_set.quickstart.dependencies_document = Document(
                id=doc.id, content=doc.content
            )
        elif doc_type == ContentKind.QUICK_START_ENTRY.value:
            document_set.quickstart.entry = doc.content
            document_set.quickstart.entry_document = Document(
                id=doc.id, content=doc.content
            )
        elif doc_type == ContentKind.QUICK_START_USE.value:
            document_set.quickstart.use = doc.content
            document_set.quickstart.use_document = Document(
                id=doc.id, content=doc.content
            )
        elif doc_type == ContentKind.TOP_LEVEL_SHORT_SENTENCE.value:
            document_set.toplevel.short_sentence = doc.content
            document_set.toplevel.short_sentence_document = Document(
                id=doc.id, content=doc.content
            )
        elif doc_type == ContentKind.TOP_LEVEL_SHORT_PARAGRAPH.value:
            document_set.toplevel.short_paragraph = doc.content
            document_set.toplevel.short_paragraph_document = Document(
                id=doc.id, content=doc.content
            )
        elif doc_type == ContentKind.TOP_LEVEL_TERSE_SENTENCE.value:
            document_set.toplevel.terse_sentence = doc.content
            document_set.toplevel.terse_sentence_document = Document(
                id=doc.id, content=doc.content
            )
        elif doc_type == ContentKind.TOP_LEVEL_LONG_DESCRIPTION.value:
            document_set.toplevel.long_description = doc.content
            document_set.toplevel.long_description_document = Document(
                id=doc.id, content=doc.content
            )
        elif doc_type == ContentKind.application_note.value:
            try:
                parsed_content = json.loads(doc.content)
                if document_set.application_notes is None:
                    document_set.application_notes = []
                document_set.application_notes.append(
                    ApplicationNote(
                        id=str(doc.id),
                        status="",
                        prompt=parsed_content.get("description", ""),
                        name=parsed_content.get("name", ""),
                        content=parsed_content.get("content", ""),
                        description=parsed_content.get("description", ""),
                        metadata=str(doc.misc_metadata) if doc.misc_metadata else "",
                        generation_timestamp=doc.created_at,
                    )
                )
            except json.JSONDecodeError as e:
                logger.warning(f"[ParseError]: {doc.id} - {e!s}")
        else:
            logger.warning(f"no ContentKind documentSet match for {doc_type}")

    if node.kind == NodeKind.CODEBASE_FILE:
        code_metadata = fetch_code_metadata(node)
        code_content = None
        if fetch_code_content:
            code_content = fetch_code_content_from_s3(node)
        document_set.code = Code(  # type: ignore
            file_name=node.relative_path.split("/")[-1],
            extension=node.relative_path.split(".")[-1],
            content=code_content,
            metadata=code_metadata,
        )

    return document_set
