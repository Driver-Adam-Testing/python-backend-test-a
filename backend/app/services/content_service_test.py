from datetime import datetime
from uuid import uuid4

import pytest
from database.derived_content_types import DerivedContentTypeNames
from database.models_v1 import (
    ChunkAndEmbedding,
    Codebase,
    DerivedContent,
    Enum_Codebase_Status,
    Enum_Derived_Content_Status,
    Workspace,
)
from fastapi import HTTPException

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
def content_service(db):
    return ContentService(db)


@pytest.fixture
def tag_service(db):
    return TagService(db)


@pytest.fixture(scope="function")
def workspace(db, current_user_with_org):
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
def codebase(db, workspace, current_user_with_org):
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
def tag(tag_service, current_user_with_org):
    new_tag_input = NewTagInput(
        name=f"TEST_TAG_{datetime.now()}", hex_color="#FFFFFF", type="tag"
    )
    tag = tag_service.create_tag(current_user_with_org, new_tag_input)
    yield tag

    # Cleanup
    tag_service.delete_tag(current_user_with_org, tag.id)


@pytest.fixture(scope="function")
def parent_content(db, workspace, codebase, content_type):
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
def source_content(db, content_service, workspace, codebase):
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
def codebase_content(content_service, current_user_with_org, workspace, codebase):
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
    content_service, current_user_with_org, workspace, codebase, codebase_content
):
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
    content_service, current_user_with_org, workspace, codebase, codebase_content
):
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
def delete_content(
    content_service, current_user_with_org, workspace, codebase, codebase_content
):
    organization_id = current_user_with_org.organization_id
    workspace_id = workspace.id
    codebase_id = codebase.id
    document_name = f"TEST_CONTENT_{datetime.now()}"
    content = content_service.create_blank_document(
        organization_id, workspace_id, codebase_id, document_name
    )
    return content


@pytest.fixture(scope="function")
def chunk_and_embed(content_service, delete_content):
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
    content_service,
    tag_service,
    current_user_with_org,
    content,
    delete_content,
    tag,
    chunk_and_embed,
    other_content,
):
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


def test_create_blank_document(
    content_service: ContentService,
    current_user_with_org,
    workspace: Workspace,
    codebase: Codebase,
    codebase_content: DerivedContent,
):
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


def test_create_application_note(content_service, current_user_with_org):
    organization_id = current_user_with_org.organization_id
    new_content = content_service.create_content(
        organization_id, CreateContentRequest(content_type="application_note")
    )
    assert new_content is not None
    assert new_content.content_type.type_name == "application_note"


def test_create_application_note_no_default_workspace(
    content_service, current_user_with_other_org
):
    organization_id = current_user_with_other_org.organization_id
    with pytest.raises(HTTPException):
        content_service.create_content(
            organization_id, CreateContentRequest(content_type="application_note")
        )


def test_create_other_content_type(content_service, current_user_with_org):
    organization_id = current_user_with_org.organization_id
    with pytest.raises(HTTPException):
        content_service.create_content(
            organization_id, CreateContentRequest(content_type="symbol")
        )


def test_get_list_content(content_service, current_user_with_org, content):
    lc_input = ListContentInput(limit=10, offset=0)
    results = content_service.get_list_content(
        current_user_with_org.organization_id, lc_input
    )
    assert results is not None
    assert results.limit == lc_input.limit
    assert results.offset == lc_input.offset


def test_get_list_content_types(content_service):
    lct_input = ListContentTypesInput(limit=10, offset=0)
    results = content_service.get_list_content_types(lct_input)
    assert results is not None
    assert len(results.results) > 0


def test_get_content_sources(content_service, current_user_with_org, content):
    response = content_service.get_content_sources(
        content.id, current_user_with_org.organization_id
    )
    assert response is not None
    assert response.results is not None


def test_get_content_by_id(content_service, current_user_with_org, content):
    fetched_content = content_service.get_content_by_id(
        content.id, current_user_with_org.organization_id
    )
    assert fetched_content is not None
    assert fetched_content.id == content.id


def test_get_content_root_by_id(content_service, current_user_with_org, content):
    root_content = content_service.get_content_root_by_id(
        content.id, current_user_with_org.organization_id
    )
    assert root_content is not None
    assert root_content.codebase_id == content.codebase_id


def test_associate_sources_with_content(
    content_service: ContentService,
    current_user_with_org,
    content: DerivedContent,
    source_content: DerivedContent,
):
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


def test_associate_invalid_sources_with_content(
    content_service, current_user_with_org, content
):
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
    content_service, current_user_with_org, content, source_content
):
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


def test_edit_content(
    content_service: ContentService, current_user_with_org, content: DerivedContent
):
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


def test_delete_content(
    content_service: ContentService,
    current_user_with_org,
    delete_content: DerivedContent,
    related_entities,
):
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
