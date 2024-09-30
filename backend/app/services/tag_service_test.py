"""
DO NOT USE try-except in tests because it masks bugs.
try:
except HTTPException as e:
Author: eric.miller@driverai.com
"""

from collections.abc import Generator
from datetime import datetime

import pytest
from database.derived_content_types import DerivedContentTypeNames
from database.models_v1 import (
    Codebase,
    DerivedContent,
    Enum_Codebase_Status,
    Enum_Derived_Content_Status,
    Tag,
    Workspace,
)
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.api.auth import CurrentUser
from app.schemas.content_schema import ListContentInput
from app.schemas.tag_schema import EditTagInput, ListTagsInput, NewTagInput
from app.services.tag_service import TagService


@pytest.fixture(scope="function")
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

    try:
        yield workspace
    finally:
        db.delete(workspace)
        db.commit()


@pytest.fixture(scope="function")
def org_b_workspace(
    db: Session, current_user_with_org: CurrentUser
) -> Generator[Workspace, None, None]:
    workspace = Workspace(display_name="Default", organization_id="org_b")
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

    try:
        yield codebase
    finally:
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

    try:
        yield tag
    finally:
        tag_service.delete_tag(current_user_with_org, tag.id)


@pytest.fixture(scope="function")
def delete_tag(tag_service: TagService, current_user_with_org: CurrentUser) -> Tag:
    new_tag_input = NewTagInput(
        name=f"TEST_TAG_{datetime.now()}", hex_color="#FFFFFF", type="tag"
    )
    tag = tag_service.create_tag(current_user_with_org, new_tag_input)
    return tag


@pytest.fixture(scope="function")
def codebase_content(
    tag_service: TagService,
    current_user_with_org: CurrentUser,
    workspace: Workspace,
    codebase: Codebase,
) -> Generator[DerivedContent, None, None]:
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
    tag_service: TagService,
    current_user_with_org: CurrentUser,
    org_b_workspace: Workspace,
    codebase: Codebase,
) -> Generator[DerivedContent, None, None]:
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
def content(
    tag_service: TagService,
    current_user_with_org: CurrentUser,
    workspace: Workspace,
    codebase: Codebase,
    codebase_content: DerivedContent,
) -> Generator[DerivedContent, None, None]:
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
    tag_service: TagService,
    current_user_with_org: CurrentUser,
    org_b_workspace: Workspace,
    codebase: Codebase,
    org_b_codebase_content: DerivedContent,
) -> Generator[DerivedContent, None, None]:
    organization_id = org_b_workspace.organization_id
    workspace_id = org_b_workspace.id
    codebase_id = codebase.id
    document_name = f"TEST_CONTENT_{datetime.now()}"
    test_content = tag_service.content_service.create_blank_document(
        organization_id, workspace_id, codebase_id, document_name
    )

    try:
        yield test_content
    finally:
        tag_service.content_service.content_repository.delete(test_content.id)


def test_create_tag(db: Session, current_user_with_org: CurrentUser) -> None:
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


def test_create_existing_tag(
    tag_service: TagService, tag: NewTagInput, current_user_with_org: CurrentUser
) -> None:
    with pytest.raises(HTTPException):
        tag_service.create_tag(
            current_user_with_org, NewTagInput(**tag.model_dump(exclude_unset=True))
        )


def test_invalid_tag_update(
    tag_service: TagService, tag: NewTagInput, current_user_with_org: CurrentUser
) -> None:
    new_name = "UPDATED_TAG"
    new_hex_color = "#000000."
    new_type = "category"
    with pytest.raises(ValidationError):
        EditTagInput(name=new_name, hex_color=new_hex_color, type=new_type)


def test_update_tag(
    tag_service: TagService, tag: NewTagInput, current_user_with_org: CurrentUser
) -> None:
    new_name = f"UPDATED_TAG_{datetime.now()}"
    new_hex_color = "#000000"
    edit_tag_input = EditTagInput(name=new_name, hex_color=new_hex_color)
    updated_tag = tag_service.edit_tag(
        current_user_with_org, str(tag.id), edit_tag_input
    )
    assert updated_tag is not None
    assert updated_tag.name == new_name
    assert updated_tag.hex_color == new_hex_color


def test_list_tags_from_other_org(
    tag_service: TagService, current_user_with_other_org: CurrentUser, tag: NewTagInput
) -> None:
    lt_input = ListTagsInput(limit=10, offset=0, name=tag.name, type=tag.type)
    tag_results = tag_service.list_tags(current_user_with_other_org, lt_input)
    assert tag_results is not None
    assert len(tag_results.results) == 0
    assert tag_results.count == 0


def test_associate_tag(
    tag_service: TagService,
    current_user_with_org: CurrentUser,
    tag: NewTagInput,
    content: DerivedContent,
) -> None:
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


def test_associate_tag_from_other_org(
    tag_service: TagService,
    current_user_with_other_org: CurrentUser,
    tag: NewTagInput,
    content: DerivedContent,
) -> None:
    content_id = content.id
    tag_id = tag.id
    include = True
    with pytest.raises(HTTPException):
        tag_service.associate_tag(
            current_user_with_other_org.organization_id, content_id, tag_id, include
        )


def test_associate_tag_content_from_other_org(
    tag_service: TagService,
    current_user_with_org: CurrentUser,
    tag: NewTagInput,
    org_b_content: DerivedContent,
) -> None:
    content_id = org_b_content.id
    tag_id = tag.id
    include = True
    with pytest.raises(HTTPException):
        tag_service.associate_tag(
            current_user_with_org.organization_id, content_id, tag_id, include
        )


def test_disassociate_tag(
    tag_service: TagService,
    current_user_with_org: CurrentUser,
    tag: NewTagInput,
    content: DerivedContent,
) -> None:
    content_id = content.id
    tag_id = tag.id
    tag_service.associate_tag(
        current_user_with_org.organization_id, content_id, tag_id, True
    )

    response = tag_service.disassociate_tag(
        current_user_with_org.organization_id, content_id, tag_id
    )
    assert response is not None


def test_disassociate_tag_from_other_org(
    tag_service: TagService,
    current_user_with_org: CurrentUser,
    tag: NewTagInput,
    content: DerivedContent,
) -> None:
    content_id = content.id
    tag_id = tag.id
    tag_service.associate_tag(
        current_user_with_org.organization_id, content_id, tag_id, True
    )

    try:
        tag_service.disassociate_tag("some_other_org", content_id, tag_id)
    except HTTPException as e:
        assert e.status_code == 404
        tag_service.disassociate_tag(
            current_user_with_org.organization_id, content_id, tag_id
        )


def test_disassociate_tag_content_from_other_org(
    tag_service: TagService,
    current_user_with_org: CurrentUser,
    tag: NewTagInput,
    org_b_content: DerivedContent,
) -> None:
    tag_id = tag.id
    with pytest.raises(HTTPException):
        tag_service.disassociate_tag(
            current_user_with_org.organization_id, org_b_content.id, tag_id
        )


def test_list_tag_contents(
    tag_service: TagService,
    current_user_with_org: CurrentUser,
    tag: NewTagInput,
    content: DerivedContent,
) -> None:
    lt_input = ListContentInput(limit=10, offset=0)
    results = tag_service.list_tag_contents(
        current_user_with_org, str(tag.id), lt_input
    )
    assert results is not None
    assert results.limit == lt_input.limit
    assert results.offset == lt_input.offset


def test_delete_tag(
    tag_service: TagService,
    current_user_with_org: CurrentUser,
    delete_tag: Tag,
) -> None:
    deleted = tag_service.delete_tag(current_user_with_org, delete_tag.id)
    assert deleted


def test_delete_tag_from_other_org(
    tag_service: TagService,
    current_user_with_other_org: CurrentUser,
    delete_tag: Tag,
) -> None:
    with pytest.raises(HTTPException):
        tag_service.delete_tag(current_user_with_other_org, delete_tag.id)
