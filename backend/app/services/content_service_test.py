"""
DO NOT USE try-except in tests because it masks bugs.
try:
except HTTPException as e:
Author: eric.miller@driverai.com
"""

import contextlib
from collections.abc import Generator
from datetime import datetime
from uuid import uuid4

import pytest
from database.derived_content_types import DerivedContentTypeNames
from database.models_v1 import (
    ChunkAndEmbedding,
    Codebase,
    DerivedContent,
    DerivedContentType,
    Enum_Codebase_Status,
    Enum_Derived_Content_Status,
    Workspace,
)
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.api.auth import CurrentUser
from app.schemas.content_schema import (
    ContentSourceAssociationItem,
    CreateContentRequest,
    ListContentInput,
    ListContentTypesInput,
)
from app.schemas.tag_schema import NewTagInput
from app.services.content_service import ContentService
from app.services.tag_service import TagService


@pytest.fixture
def content_service(db: Session) -> ContentService:
    return ContentService(db)


@pytest.fixture
def tag_service(db: Session) -> TagService:
    return TagService(db)


@pytest.fixture(scope="function")
def workspace(
    db: Session, current_user_with_org: CurrentUser
) -> Generator[Workspace, None, None]:
    workspace = Workspace(
        display_name="Default",
        organization_id=current_user_with_org.organization_id,
    )
    db.add(workspace)
    db.commit()
    yield workspace

    # Cleanup
    db.rollback()  # Ensure rollback before delete
    db.delete(workspace)
    db.commit()


@pytest.fixture(scope="function")
def org_b_workspace(
    db: Session, current_user_with_other_org: CurrentUser
) -> Generator[Workspace, None, None]:
    workspace = Workspace(
        display_name="Default",
        organization_id=current_user_with_other_org.organization_id,
    )
    db.add(workspace)
    db.commit()

    try:
        yield workspace
    finally:
        db.delete(workspace)
        db.commit()


@pytest.fixture(scope="function")
def codebase(
    db: Session, workspace: Workspace, current_user_with_org: CurrentUser
) -> Generator[Codebase, None, None]:
    codebase = Codebase(
        workspace_id=workspace.id,
        codebase_name="TEST_CODEBASE",
        description="TEST_DESCRIPTION",
        status=Enum_Codebase_Status.processing_complete.value,
        storage_url="TEST_STORAGE_URL",
        resource_root="TEST_CODEBASE/",
        creator_id=current_user_with_org.user_id,
    )
    db.add(codebase)
    db.commit()
    yield codebase

    # Cleanup
    db.rollback()  # Ensure rollback before delete
    db.delete(codebase)
    db.commit()


@pytest.fixture(scope="function")
def tag(
    tag_service: TagService, current_user_with_org: CurrentUser
) -> Generator[NewTagInput, None, None]:
    new_tag_input = NewTagInput(
        name=f"TEST_TAG_{datetime.now()}", hex_color="#FFFFFF", type="tag"
    )
    tag = tag_service.create_tag(current_user_with_org, new_tag_input)
    yield tag

    # Cleanup
    tag_service.delete_tag(current_user_with_org, tag.id)


@pytest.fixture(scope="function")
def parent_content(
    db: Session,
    workspace: Workspace,
    codebase: Codebase,
    content_type: DerivedContentType,
) -> Generator[DerivedContent, None, None]:
    parent_content = DerivedContent(
        content_type_id=content_type.id,
        workspace_id=workspace.id,
        codebase_id=codebase.id,
        relative_path=codebase.codebase_name,
        misc_metadata={},
        status=Enum_Derived_Content_Status.generation_complete,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    db.add(parent_content)
    db.commit()
    yield parent_content

    # Cleanup
    db.delete(parent_content)
    db.commit()


@pytest.fixture(scope="function")
def source_content(
    db: Session,
    content_service: ContentService,
    workspace: Workspace,
    codebase: Codebase,
) -> Generator[DerivedContent, None, None]:
    content_type_id = (
        content_service.derived_content_type_repository.get_by_type_name(
            DerivedContentTypeNames.CODEBASE.value
        )
    ).id
    source_content = DerivedContent(
        content_type_id=content_type_id,
        workspace_id=workspace.id,
        codebase_id=codebase.id,
        relative_path=codebase.codebase_name,
        misc_metadata={},
        status=Enum_Derived_Content_Status.generation_complete,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    db.add(source_content)
    db.commit()
    yield source_content

    # Cleanup
    db.rollback()  # Ensure rollback before delete
    db.delete(source_content)
    db.commit()


@pytest.fixture(scope="function")
def codebase_content(
    content_service: ContentService,
    current_user_with_org: CurrentUser,
    workspace: Workspace,
    codebase: Codebase,
) -> Generator[DerivedContent, None, None]:
    workspace_id = workspace.id
    codebase_id = codebase.id
    content_type_id = (
        content_service.derived_content_type_repository.get_by_type_name(
            DerivedContentTypeNames.CODEBASE.value
        )
    ).id
    codebase_record = DerivedContent(
        content_type_id=content_type_id,
        workspace_id=workspace_id,
        codebase_id=codebase_id,
        relative_path=codebase.codebase_name,
        misc_metadata={},
        status=Enum_Derived_Content_Status.generation_complete,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    content_service.content_repository.create(codebase_record)
    yield codebase_record

    # Cleanup
    content_service.content_repository.session.rollback()  # Ensure rollback before delete
    content_service.content_repository.delete(codebase_record.id)


@pytest.fixture(scope="function")
def content(
    content_service: ContentService,
    current_user_with_org: CurrentUser,
    workspace: Workspace,
    codebase: Codebase,
    codebase_content: DerivedContent,
) -> Generator[DerivedContent, None, None]:
    organization_id = current_user_with_org.organization_id
    workspace_id = workspace.id
    codebase_id = codebase.id
    document_name = f"TEST_CONTENT_{datetime.now()}"
    content = content_service.create_blank_document(
        organization_id, workspace_id, codebase_id, document_name
    )
    yield content

    # Cleanup
    content_service.content_repository.session.rollback()  # Ensure rollback before delete
    content_service.content_repository.delete(content.id)


@pytest.fixture(scope="function")
def other_content(
    content_service: ContentService,
    current_user_with_org: CurrentUser,
    workspace: Workspace,
    codebase: Codebase,
    codebase_content: DerivedContent,
) -> Generator[DerivedContent, None, None]:
    organization_id = current_user_with_org.organization_id
    workspace_id = workspace.id
    codebase_id = codebase.id
    document_name = f"TEST_CONTENT_{datetime.now()}"
    content = content_service.create_blank_document(
        organization_id, workspace_id, codebase_id, document_name
    )
    yield content

    # Cleanup
    content_service.content_repository.session.rollback()  # Ensure rollback before delete
    content_service.content_repository.delete(content.id)


@pytest.fixture(scope="function")
def org_b_content(
    content_service: ContentService,
    current_user_with_org: CurrentUser,
    org_b_workspace: Workspace,
    codebase: Codebase,
) -> Generator[DerivedContent, None, None]:
    organization_id = current_user_with_org.organization_id
    test_content = content_service.create_content(
        organization_id, CreateContentRequest(content_type="application_note")
    )

    try:
        yield test_content
    finally:
        content_service.content_repository.delete(test_content.id)


@pytest.fixture(scope="function")
def delete_content(
    content_service: ContentService,
    current_user_with_org: CurrentUser,
    workspace: Workspace,
    codebase: Codebase,
    codebase_content: DerivedContent,
) -> DerivedContent:
    organization_id = current_user_with_org.organization_id
    workspace_id = workspace.id
    codebase_id = codebase.id
    document_name = f"TEST_CONTENT_{datetime.now()}"
    content = content_service.create_blank_document(
        organization_id, workspace_id, codebase_id, document_name
    )
    return content


@pytest.fixture(scope="function")
def chunk_and_embed(
    content_service: ContentService, delete_content: DerivedContent
) -> ChunkAndEmbedding:
    chunk_and_embed = ChunkAndEmbedding(
        content_id=delete_content.id,
        text="TEST_CHUNK_AND_EMBED",
        chunk_number=1,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    content_service.session.add(chunk_and_embed)
    content_service.session.commit()
    return chunk_and_embed


@pytest.fixture(scope="function")
def related_entities(
    content_service: ContentService,
    tag_service: TagService,
    current_user_with_org: CurrentUser,
    content: DerivedContent,
    delete_content: DerivedContent,
    tag: NewTagInput,
    chunk_and_embed: ChunkAndEmbedding,
    other_content: DerivedContent,
) -> list:
    # Associate content with delete_content
    content_source_associations = [
        ContentSourceAssociationItem(source_content_id=delete_content.id, include=True)
    ]
    # Associate source content with content
    content_service.associate_sources_with_content(
        current_user_with_org.organization_id, content.id, content_source_associations
    )
    other_content_source_associations = [
        ContentSourceAssociationItem(source_content_id=other_content.id, include=True)
    ]
    # Associate source content with delete_content
    content_service.associate_sources_with_content(
        current_user_with_org.organization_id,
        delete_content.id,
        other_content_source_associations,
    )
    # Associate tag with delete_content
    tag_service.associate_tag(
        current_user_with_org.organization_id, delete_content.id, tag.id
    )

    return [delete_content, content, tag, chunk_and_embed]


@pytest.fixture(scope="function")
def complete_codebase_with_related_entities(
    db: Session,
    content_service: ContentService,
    current_user_with_org: CurrentUser,
    workspace: Workspace,
) -> DerivedContent:
    """
    Create a complete codebase with related entities
    """
    # Create a codebase
    codebase = Codebase(
        workspace_id=workspace.id,
        codebase_name="TEST_CODEBASE",
        description="TEST_DESCRIPTION",
        status=Enum_Codebase_Status.processing_complete.value,
        storage_url="TEST_STORAGE_URL",
        resource_root="TEST_CODEBASE/",
        creator_id=current_user_with_org.user_id,
    )
    db.add(codebase)
    db.commit()

    codebase_content_type_id = (
        content_service.derived_content_type_repository.get_by_type_name(
            DerivedContentTypeNames.CODEBASE.value
        )
    ).id
    codebase_directory_content_type_id = (
        content_service.derived_content_type_repository.get_by_type_name(
            DerivedContentTypeNames.CODEBASE_DIRECTORY.value
        )
    ).id
    codebase_file_content_type_id = (
        content_service.derived_content_type_repository.get_by_type_name(
            DerivedContentTypeNames.CODEBASE_FILE.value
        )
    ).id
    codebase_source_content_records = [
        {
            "content_type_id": codebase_content_type_id,
            "source_content_id": None,
            "content": None,
            "metadata": {},
            "status": "generation-complete",
            "order": 0,
            "relative_path": "TEST_CODEBASE",
            "workspace_id": workspace.id,
            "codebase_id": codebase.id,
            "content_name": None,
        },
        {
            "content_type_id": codebase_directory_content_type_id,
            "source_content_id": None,
            "content": None,
            "metadata": {},
            "status": "generation-complete",
            "order": 0,
            "relative_path": "TEST_CODEBASE/",
            "workspace_id": workspace.id,
            "codebase_id": codebase.id,
            "content_name": None,
        },
        {
            "content_type_id": codebase_file_content_type_id,
            "source_content_id": None,
            "content": None,
            "metadata": {},
            "status": "generation-complete",
            "order": 0,
            "relative_path": "TEST_CODEBASE/README.md",
            "workspace_id": workspace.id,
            "codebase_id": codebase.id,
            "content_name": None,
        },
        {
            "content_type_id": codebase_file_content_type_id,
            "source_content_id": None,
            "content": None,
            "metadata": {
                "size": 957,
                "sloc": 33,
                "is_hex": False,
                "extension": "",
                "is_binary": False,
                "is_analyzable": True,
                "is_blacklisted": False,
            },
            "status": "generation-complete",
            "order": 0,
            "relative_path": "TEST_CODEBASE/main.py",
            "workspace_id": workspace.id,
            "codebase_id": codebase.id,
            "content_name": None,
        },
        {
            "content_type_id": codebase_file_content_type_id,
            "source_content_id": None,
            "content": None,
            "metadata": {
                "size": 957,
                "sloc": 33,
                "is_hex": False,
                "extension": "",
                "is_binary": False,
                "is_analyzable": True,
                "is_blacklisted": False,
            },
            "status": "generation-complete",
            "order": 0,
            "relative_path": "TEST_CODEBASE/main_test.py",
            "workspace_id": workspace.id,
            "codebase_id": codebase.id,
            "content_name": None,
        },
    ]
    records = []
    codebase_record = None

    for record in codebase_source_content_records:
        content = DerivedContent(**record)
        if content.content_type_id == codebase_content_type_id:
            codebase_record = content

        records.append(content)
        db.add(content)
        db.commit()

    ld_content_type_id = (
        content_service.derived_content_type_repository.get_by_type_name(
            DerivedContentTypeNames.LONG_DESCRIPTION.value
        )
    ).id
    sd_content_type_id = (
        content_service.derived_content_type_repository.get_by_type_name(
            DerivedContentTypeNames.SHORT_SENTENCE_DESCRIPTION.value
        )
    ).id
    spd_content_type_id = (
        content_service.derived_content_type_repository.get_by_type_name(
            DerivedContentTypeNames.SHORT_PARAGRAPH_DESCRIPTION.value
        )
    ).id

    # add revived content to each
    TECH_DOC_TEXT_IRS = {
        DerivedContentTypeNames.LONG_DESCRIPTION.value: "To get started with the `TEST_CODEBASE` codebase, begin by setting up the containerized environment using the `READMD.md` located at `TEST_CODEBASE/README.md`.",
        DerivedContentTypeNames.SHORT_SENTENCE_DESCRIPTION.value: "# Some overview text in markdown.",
        DerivedContentTypeNames.SHORT_PARAGRAPH_DESCRIPTION.value: "The `main.py` in the `TEST_CODEBASE` codebase sets up a multi-stage build environment for a Python FastAPI application, installing dependencies, building the application, and preparing it for production deployment.",
    }
    # for i, record in enumerate(codebase_source_content_records):
    for record in records:
        long_description = DerivedContent(
            content_type_id=ld_content_type_id,
            content=TECH_DOC_TEXT_IRS[DerivedContentTypeNames.LONG_DESCRIPTION.value],
            workspace_id=workspace.id,
            codebase_id=codebase.id,
            source_content_id=record.id,
            status=Enum_Derived_Content_Status.generation_complete,
            metadata={},
            relative_path=record.relative_path,
            order=0,
        )
        short_sentence_description = DerivedContent(
            content_type_id=sd_content_type_id,
            content=TECH_DOC_TEXT_IRS[
                DerivedContentTypeNames.SHORT_SENTENCE_DESCRIPTION.value
            ],
            workspace_id=workspace.id,
            codebase_id=codebase.id,
            source_content_id=record.id,
            status=Enum_Derived_Content_Status.generation_complete,
            metadata={},
            relative_path=record.relative_path,
            order=0,
        )
        short_paragraph_description = DerivedContent(
            content_type_id=spd_content_type_id,
            content=TECH_DOC_TEXT_IRS[
                DerivedContentTypeNames.SHORT_PARAGRAPH_DESCRIPTION.value
            ],
            workspace_id=workspace.id,
            codebase_id=codebase.id,
            source_content_id=record.id,
            status=Enum_Derived_Content_Status.generation_complete,
            metadata={},
            relative_path=record.relative_path,
            order=0,
        )
        db.add_all(
            [
                long_description,
                short_sentence_description,
                short_paragraph_description,
            ]
        )

    db.commit()
    print(f"Codebase content created for {codebase_record.codebase_id}")
    return codebase_record


def test_create_blank_document(
    content_service: ContentService,
    current_user_with_org: CurrentUser,
    workspace: Workspace,
    codebase: Codebase,
    codebase_content: DerivedContent,
) -> None:
    organization_id = current_user_with_org.organization_id
    workspace_id = workspace.id
    codebase_id = codebase.id
    document_name = f"TEST_CONTENT_{datetime.now()}"
    new_content = content_service.create_blank_document(
        organization_id, workspace_id, codebase_id, document_name
    )
    assert new_content is not None
    assert new_content.workspace_id == workspace_id
    assert new_content.codebase_id == codebase_id
    assert new_content.content_type_id is not None
    content_service.content_repository.delete(new_content.id)


def test_create_application_note(
    content_service: ContentService, current_user_with_org: CurrentUser
) -> None:
    organization_id = current_user_with_org.organization_id
    new_content = content_service.create_content(
        organization_id, CreateContentRequest(content_type="application_note")
    )
    assert new_content is not None
    assert new_content.content_type.type_name == "application_note"


def test_create_application_note_no_default_workspace(
    content_service: ContentService, current_user_with_other_org: CurrentUser
) -> None:
    organization_id = current_user_with_other_org.organization_id
    with pytest.raises(HTTPException):
        content_service.create_content(
            organization_id, CreateContentRequest(content_type="application_note")
        )


def test_create_other_content_type(
    content_service: ContentService, current_user_with_org: CurrentUser
) -> None:
    organization_id = current_user_with_org.organization_id
    with pytest.raises(HTTPException):
        content_service.create_content(
            organization_id, CreateContentRequest(content_type="symbol")
        )


def test_get_list_content(
    content_service: ContentService,
    current_user_with_org: CurrentUser,
    content: DerivedContent,
) -> None:
    lc_input = ListContentInput(limit=10, offset=0)
    results = content_service.get_list_content(
        current_user_with_org.organization_id, lc_input
    )
    assert results is not None
    assert results.limit == lc_input.limit
    assert results.offset == lc_input.offset


def test_get_list_content_from_other_org(
    content_service: ContentService,
    current_user_with_other_org: CurrentUser,
    content: DerivedContent,
) -> None:
    lc_input = ListContentInput(limit=10, offset=0)
    results = content_service.get_list_content(
        current_user_with_other_org.organization_id, lc_input
    )
    assert results is not None
    assert len(results.results) == 0
    assert results.count == 0


def test_get_list_content_types(content_service: ContentService) -> None:
    lct_input = ListContentTypesInput(limit=10, offset=0)
    results = content_service.get_list_content_types(lct_input)
    assert results is not None
    assert len(results.results) > 0


def test_get_content_sources(
    content_service: ContentService,
    current_user_with_org: CurrentUser,
    content: DerivedContent,
) -> None:
    response = content_service.get_content_sources(
        content.id, current_user_with_org.organization_id
    )
    assert response is not None
    assert response.results is not None


def test_get_content_sources_from_other_org(
    content_service: ContentService,
    current_user_with_other_org: CurrentUser,
    content: DerivedContent,
) -> None:
    with pytest.raises(HTTPException):
        content_service.get_content_sources(
            content.id, current_user_with_other_org.organization_id
        )


def test_get_content_by_id(
    content_service: ContentService,
    current_user_with_org: CurrentUser,
    content: DerivedContent,
) -> None:
    fetched_content = content_service.get_content_by_id(
        content.id, current_user_with_org.organization_id
    )
    assert fetched_content is not None
    assert fetched_content.id == content.id


def test_get_content_by_id_from_other_org(
    content_service: ContentService,
    current_user_with_other_org: CurrentUser,
    content: DerivedContent,
) -> None:
    with pytest.raises(HTTPException):
        content_service.get_content_by_id(
            content.id, current_user_with_other_org.organization_id
        )


def test_get_content_root_by_id(
    content_service: ContentService,
    current_user_with_org: CurrentUser,
    content: DerivedContent,
) -> None:
    root_content = content_service.get_content_root_by_id(
        content.id, current_user_with_org.organization_id
    )
    assert root_content is not None
    assert root_content.codebase_id == content.codebase_id


def test_get_content_root_by_id_from_other_org(
    content_service: ContentService,
    current_user_with_other_org: CurrentUser,
    content: DerivedContent,
) -> None:
    with pytest.raises(HTTPException):
        content_service.get_content_root_by_id(
            content.id, current_user_with_other_org.organization_id
        )


def test_associate_sources_with_content(
    content_service: ContentService,
    current_user_with_org: CurrentUser,
    content: DerivedContent,
    source_content: DerivedContent,
) -> None:
    content_id = content.id
    source_content_id = source_content.id
    content_source_associations = [
        ContentSourceAssociationItem(source_content_id=source_content_id, include=True)
    ]
    response = content_service.associate_sources_with_content(
        current_user_with_org.organization_id, content_id, content_source_associations
    )
    assert response is not None
    assert response.content_id == content_id
    assert len(response.sources) == 1
    assert response.sources[0].source_content_id == source_content_id

    content_service.disassociate_document_source(
        current_user_with_org.organization_id, content_id, source_content_id
    )


def test_associate_sources_with_content_from_other_org(
    content_service: ContentService,
    current_user_with_other_org: CurrentUser,
    content: DerivedContent,
    source_content: DerivedContent,
) -> None:
    content_id = content.id
    source_content_id = source_content.id
    content_source_associations = [
        ContentSourceAssociationItem(source_content_id=source_content_id, include=True)
    ]
    with pytest.raises(HTTPException):
        content_service.associate_sources_with_content(
            current_user_with_other_org.organization_id,
            content_id,
            content_source_associations,
        )


def test_associate_invalid_sources_with_content(
    content_service: ContentService,
    current_user_with_org: CurrentUser,
    content: DerivedContent,
) -> None:
    content_id = content.id
    source_content_id = uuid4()
    content_source_associations = [
        ContentSourceAssociationItem(source_content_id=source_content_id, include=True)
    ]
    with pytest.raises(HTTPException):
        content_service.associate_sources_with_content(
            current_user_with_org.organization_id,
            content_id,
            content_source_associations,
        )


def test_disassociate_document_source(
    content_service: ContentService,
    current_user_with_org: CurrentUser,
    content: DerivedContent,
    source_content: DerivedContent,
) -> None:
    content_id = content.id
    source_content_id = source_content.id
    content_service.associate_sources_with_content(
        current_user_with_org.organization_id,
        content_id,
        [
            ContentSourceAssociationItem(
                source_content_id=source_content_id, include=True
            )
        ],
    )

    response = content_service.disassociate_document_source(
        current_user_with_org.organization_id, content_id, source_content_id
    )
    assert response is not None
    assert response.document_id == content_id
    assert response.source_id == source_content_id


def test_disassociate_document_source_from_other_org(
    content_service: ContentService,
    current_user_with_org: CurrentUser,
    content: DerivedContent,
    source_content: DerivedContent,
) -> None:
    content_id = content.id
    source_content_id = source_content.id
    content_service.associate_sources_with_content(
        current_user_with_org.organization_id,
        content_id,
        [
            ContentSourceAssociationItem(
                source_content_id=source_content_id, include=True
            )
        ],
    )

    try:
        with pytest.raises(HTTPException):
            content_service.disassociate_document_source(
                "some_other_org", content_id, source_content_id
            )
        response = content_service.disassociate_document_source(
            current_user_with_org.organization_id, content_id, source_content_id
        )
        assert response is not None
        assert response.document_id == content_id
        assert response.source_id == source_content_id
    finally:
        # Cleanup
        with contextlib.suppress(
            HTTPException
        ):  # this is to prevent the test from failing if the cleanup already happened
            content_service.disassociate_document_source(
                current_user_with_org.organization_id, content_id, source_content_id
            )


def test_edit_content(
    content_service: ContentService,
    current_user_with_org: CurrentUser,
    content: DerivedContent,
) -> None:
    organization_id = current_user_with_org.organization_id
    content_id = content.id
    new_content = {
        "content_name": "Updated Content Name",
        "content": "Updated content",
        "misc_metadata": {"key": "value"},
    }

    updated_content = content_service.edit_content(
        organization_id, content_id, new_content
    )

    assert updated_content is not None
    assert updated_content.id == content_id
    assert updated_content.content_name == "Updated Content Name"
    assert updated_content.content == "Updated content"
    assert updated_content.misc_metadata == {"key": "value"}


def test_edit_content_from_other_org(
    content_service: ContentService,
    current_user_with_other_org: CurrentUser,
    content: DerivedContent,
) -> None:
    organization_id = current_user_with_other_org.organization_id
    content_id = content.id
    new_content = {
        "content_name": "Updated Content Name",
        "content": "Updated content",
        "misc_metadata": {"key": "value"},
    }
    with pytest.raises(HTTPException):
        content_service.edit_content(organization_id, content_id, new_content)


def test_delete_content(
    content_service: ContentService,
    current_user_with_org: CurrentUser,
    delete_content: DerivedContent,
    related_entities: list,
) -> None:
    """
    Test that content can be deleted
    related_entities: creates  source_content, tag, chunk_and_embed
    """
    organization_id = current_user_with_org.organization_id
    content_id = delete_content.id

    # Ensure the content exists before deletion
    fetched_content = content_service.get_content_by_id(content_id, organization_id)
    assert fetched_content is not None

    # Delete the content
    content_service.delete_content(organization_id, content_id)

    # Ensure the content no longer exists after deletion
    with pytest.raises(
        HTTPException
    ):  # Replace with the actual exception your service raises
        content_service.get_content_by_id(content_id, organization_id)


def test_delete_content_from_other_org(
    content_service: ContentService,
    current_user_with_org: CurrentUser,
    delete_content: DerivedContent,
    related_entities: list,
) -> None:
    """
    Test that content can be deleted
    related_entities: creates  source_content, tag, chunk_and_embed
    """
    organization_id = current_user_with_org.organization_id
    content_id = delete_content.id

    try:
        with pytest.raises(HTTPException):
            content_service.delete_content("some_other_org", content_id)
    finally:
        content_service.delete_content(organization_id, content_id)

    # Ensure the content no longer exists after deletion
    with pytest.raises(
        HTTPException
    ):  # Replace with the actual exception your service raises
        content_service.get_content_by_id(content_id, organization_id)


def test_delete_codebase(
    content_service: ContentService,
    current_user_with_org: CurrentUser,
    complete_codebase_with_related_entities: DerivedContent,
) -> None:
    organization_id = current_user_with_org.organization_id
    content_id = complete_codebase_with_related_entities.id
    content_service.delete_content(organization_id, content_id)


def test_delete_codebase_from_other_org(
    content_service: ContentService,
    current_user_with_org: CurrentUser,
    complete_codebase_with_related_entities: DerivedContent,
) -> None:
    organization_id = current_user_with_org.organization_id
    content_id = complete_codebase_with_related_entities.id
    try:
        with pytest.raises(HTTPException):
            content_service.delete_content("some_other_org", content_id)

    finally:
        content_service.delete_content(organization_id, content_id)
