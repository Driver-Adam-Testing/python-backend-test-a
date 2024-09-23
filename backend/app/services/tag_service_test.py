from datetime import datetime

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
from pydantic import ValidationError

from app.schemas.content_schema import ListContentInput
from app.schemas.tag_schema import EditTagInput, ListTagsInput, NewTagInput
from app.services.tag_service import TagService


@pytest.fixture(scope="function")
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

    try:
        yield workspace
    finally:
        db.delete(workspace)
        db.commit()


@pytest.fixture(scope="function")
def org_b_workspace(db, current_user_with_org):
    workspace = Workspace(display_name="Default", organization_id="org_b")
    db.add(workspace)
    db.commit()

    try:
        yield workspace
    finally:
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

    try:
        yield codebase
    finally:
        db.delete(codebase)
        db.commit()


@pytest.fixture(scope="function")
def tag(tag_service, current_user_with_org):
    new_tag_input = NewTagInput(
        name=f"TEST_TAG_{datetime.now()}", hex_color="#FFFFFF", type="tag"
    )
    tag = tag_service.create_tag(current_user_with_org, new_tag_input)

    try:
        yield tag
    finally:
        tag_service.delete_tag(current_user_with_org, tag.id)


@pytest.fixture(scope="function")
def codebase_content(tag_service, current_user_with_org, workspace, codebase):
    workspace_id = workspace.id
    codebase_id = codebase.id
    content_type_id = (
        tag_service.content_service.derived_content_type_repository.get_by_type_name(
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
    codebase_content = tag_service.content_service.content_repository.create(
        codebase_record
    )

    try:
        yield codebase_content
    finally:
        tag_service.content_service.content_repository.delete(codebase_content.id)


@pytest.fixture(scope="function")
def org_b_codebase_content(
    tag_service, current_user_with_org, org_b_workspace, codebase
):
    workspace_id = org_b_workspace.id
    codebase_id = codebase.id
    content_type_id = (
        tag_service.content_service.derived_content_type_repository.get_by_type_name(
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
    codebase_content = tag_service.content_service.content_repository.create(
        codebase_record
    )

    try:
        yield codebase_content
    finally:
        tag_service.content_service.content_repository.delete(codebase_content.id)


@pytest.fixture(scope="function")
def content(tag_service, current_user_with_org, workspace, codebase, codebase_content):
    organization_id = current_user_with_org.organization_id
    workspace_id = workspace.id
    codebase_id = codebase.id
    document_name = f"TEST_CONTENT_{datetime.now()}"
    content = tag_service.content_service.create_blank_document(
        organization_id, workspace_id, codebase_id, document_name
    )

    try:
        yield content
    finally:
        tag_service.content_service.content_repository.delete(content.id)


@pytest.fixture(scope="function")
def org_b_content(
    tag_service,
    current_user_with_org,
    org_b_workspace,
    codebase,
    org_b_codebase_content,
):
    organization_id = org_b_workspace.organization_id
    workspace_id = org_b_workspace.id
    codebase_id = codebase.id
    document_name = f"TEST_CONTENT_{datetime.now()}"
    content = tag_service.content_service.create_blank_document(
        organization_id, workspace_id, codebase_id, document_name
    )

    try:
        yield content
    finally:
        tag_service.content_service.content_repository.delete(content.id)


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


def test_create_tag(db, current_user_with_org):
    tag_service = TagService(db)
    new_tag_input = NewTagInput(
        name=f"TEST_TAG_{datetime.now()}", hex_color="#FFFFFF", type="tag"
    )
    new_tag = tag_service.create_tag(current_user_with_org, new_tag_input)
    assert new_tag is not None
    assert new_tag.name == new_tag_input.name
    assert new_tag.hex_color == new_tag_input.hex_color
    assert new_tag.type == new_tag_input.type
    assert new_tag.organization_id == current_user_with_org.organization_id
    assert new_tag.created_by == current_user_with_org.user_id


# There doesn't seem to be a unique constraint on name+org_id, so
# the IntegrityError's aren't ever being triggered in this implementation.
# def test_create_existing_tag(tag_service, current_user_with_org):
#     with pytest.raises(HTTPException):
#         new_tag_input = NewTagInput(name="TEST_TAG", hex_color="#FFFFFF", type="tag")
#         tag_service.create_tag(
#             current_user_with_org,
#             NewTagInput(**new_tag_input.model_dump(exclude_unset=True)),
#         )


def test_invalid_tag_update(tag_service, tag, current_user_with_org):
    new_name = "UPDATED_TAG"
    new_hex_color = "#000000."
    new_type = "category"
    with pytest.raises(ValidationError):
        EditTagInput(name=new_name, hex_color=new_hex_color, type=new_type)


def test_update_tag(tag_service, tag, current_user_with_org):
    new_name = f"UPDATED_TAG_{datetime.now()}"
    new_hex_color = "#000000"
    edit_tag_input = EditTagInput(name=new_name, hex_color=new_hex_color)
    updated_tag = tag_service.edit_tag(
        current_user_with_org, str(tag.id), edit_tag_input
    )
    assert updated_tag is not None
    assert updated_tag.name == new_name
    assert updated_tag.hex_color == new_hex_color


def test_list_tags(tag_service, current_user_with_org, tag):
    lt_input = ListTagsInput(limit=10, offset=0, name=tag.name, type=tag.type)
    results = tag_service.list_tags(current_user_with_org, lt_input)
    assert results is not None
    assert results.limit == lt_input.limit
    assert results.offset == lt_input.offset


def test_associate_tag(tag_service, current_user_with_org, tag, content):
    content_id = content.id
    tag_id = tag.id
    include = True
    response = tag_service.associate_tag(
        current_user_with_org.organization_id, content_id, tag_id, include
    )
    assert response is not None

    response = tag_service.disassociate_tag(
        current_user_with_org.organization_id, content_id, tag_id
    )
    assert response is not None


def test_associate_tag_from_other_org(tag_service, current_user_with_org, tag, content):
    content_id = content.id
    tag_id = tag.id
    include = True
    with pytest.raises(HTTPException):
        tag_service.associate_tag("some_other_org", content_id, tag_id, include)


def test_associate_tag_content_from_other_org(
    tag_service, current_user_with_org, tag, org_b_content
):
    content_id = org_b_content.id
    tag_id = tag.id
    include = True
    with pytest.raises(HTTPException):
        tag_service.associate_tag(
            current_user_with_org.organization_id, content_id, tag_id, include
        )


def test_disassociate_tag(tag_service, current_user_with_org, tag, content):
    content_id = content.id
    tag_id = tag.id
    tag_service.associate_tag(
        current_user_with_org.organization_id, content_id, tag_id, True
    )

    response = tag_service.disassociate_tag(
        current_user_with_org.organization_id, content_id, tag_id
    )
    assert response is not None


def test_list_tag_contents(tag_service, current_user_with_org, tag, content):
    lt_input = ListContentInput(limit=10, offset=0)
    results = tag_service.list_tag_contents(
        current_user_with_org, str(tag.id), lt_input
    )
    assert results is not None
    assert results.limit == lt_input.limit
    assert results.offset == lt_input.offset
