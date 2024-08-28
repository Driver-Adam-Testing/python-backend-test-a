from datetime import datetime
from unittest.mock import Mock
from uuid import uuid4

import pytest
from database.derived_content_types import DerivedContentTypeNames
from database.models_v1 import (
    Codebase,
    DerivedContent,
    DerivedContentType,
    Enum_Codebase_Status,
    Enum_Derived_Content_Status,
    Workspace,
)
from fastapi import HTTPException
from sqlalchemy.exc import NoResultFound

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
def content_service(db):
    return ContentService(db)


@pytest.fixture
def tag_service(db):
    return TagService(db)


@pytest.fixture(scope="function", autouse=True)
def create_content_types(db):
    try:
        for type_name in DerivedContentTypeNames:
            content_type = DerivedContentType(
                type_name=type_name.value
            )  # Convert enum to its value
            db.add(content_type)
        db.commit()

    except Exception as e:
        print(e)
        db.rollback()


@pytest.fixture
def workspace(db, current_user_with_org):
    workspace = Workspace(
        display_name="Default",
        organization_id=current_user_with_org.organization_id,
    )
    db.add(workspace)
    db.commit()
    return workspace


@pytest.fixture
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
    return codebase


@pytest.fixture
def tag(tag_service, current_user_with_org):
    new_tag_input = NewTagInput(
        name=f"TEST_TAG_{datetime.now()}", hex_color="#FFFFFF", type="tag"
    )
    return tag_service.create_tag(current_user_with_org, new_tag_input)


# @pytest.fixture
# def content_type(db):
#     content_type = DerivedContentType(type_name=DerivedContentTypeNames.CODEBASE.value)
#     db.add(content_type)
#     db.commit()
#     return content_type


@pytest.fixture
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
    return parent_content


@pytest.fixture
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
    return source_content


@pytest.fixture
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
    return content_service.content_repository.create(codebase_record)


@pytest.fixture
def content(
    content_service, current_user_with_org, workspace, codebase, codebase_content
):
    organization_id = current_user_with_org.organization_id
    workspace_id = workspace.id
    codebase_id = codebase.id
    document_name = f"TEST_CONTENT_{datetime.now()}"
    return content_service.create_blank_document(
        organization_id, workspace_id, codebase_id, document_name
    )


@pytest.fixture(scope="function")
def current_user_with_org_no_workspace() -> CurrentUser:
    current_user = Mock(spec=CurrentUser)
    current_user.user_id = "other_test_user_id"
    current_user.organization_id = "other_test_org_id"
    current_user.is_service_account = False
    return current_user


def test_create_blank_document(
    content_service, current_user_with_org, workspace, codebase, codebase_content
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


def test_create_application_note(content_service, current_user_with_org):
    organization_id = current_user_with_org.organization_id
    new_content = content_service.create_content(
        organization_id, CreateContentRequest(content_type="application_note")
    )
    assert new_content is not None
    assert new_content.content_type.type_name == "application_note"


def test_create_application_note_no_default_workspace(
    content_service, current_user_with_org_no_workspace
):
    organization_id = current_user_with_org_no_workspace.organization_id
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


def test_create_document_from_template(content_service, current_user_with_org, content):
    with pytest.raises(NoResultFound):
        content_service.create_document_from_template(
            current_user_with_org.organization_id, content.id
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


def test_create_template(content_service, current_user_with_org, workspace, codebase):
    with pytest.raises(NoResultFound):
        content_service.create_template(
            current_user_with_org.organization_id, workspace.id, codebase.id
        )


def test_associate_tag(content_service, current_user_with_org, content, tag):
    content_id = content.id
    tag_id = tag.id
    include = True
    response = content_service.associate_tag(
        current_user_with_org.organization_id, content_id, tag_id, include
    )
    assert response is not None
    assert response.tag_id == tag_id
    assert response.content_id == content_id


def test_associate_tag_from_other_org(
    content_service, current_user_with_org, content, tag
):
    content_id = content.id
    tag_id = tag.id
    include = True
    with pytest.raises(HTTPException):
        content_service.associate_tag("some_other_org", content_id, tag_id, include)


def test_disassociate_tag(content_service, current_user_with_org, content, tag):
    content_id = content.id
    tag_id = tag.id
    content_service.associate_tag(
        current_user_with_org.organization_id, content_id, tag_id, True
    )

    response = content_service.disassociate_tag(
        current_user_with_org.organization_id, content_id, tag_id
    )
    assert response is not None
    assert response.tag_id == tag_id
    assert response.content_id == content_id


def test_associate_sources_with_content(
    content_service, current_user_with_org, content, source_content
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
