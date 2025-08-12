# TODO: removed for now since we can't currently run tests that hit the db
# We need a better db-in-the-loop test scheme first.

# """
# DO NOT USE try-except in tests because it masks bugs.
# try:
# except HTTPException as e:
# Author: eric.miller@driverai.com
# """
#
# from collections.abc import Generator
# from datetime import datetime
#
# import pytest
# from database.models_v1 import (
#     DerivedContent,
#     Tag,
# )
# from fastapi import HTTPException
# from pydantic import ValidationError
# from sqlalchemy.orm import Session
#
# from app.api.auth import UserToken
# from app.schemas.content_schema import ListContentInput
# from app.schemas.tag_schema import EditTagInput, ListTagsInput, NewTagInput
# from app.services.tag_service import TagService
#
# #
# # @pytest.fixture(scope="function")
# # def tag_service(db: Session) -> TagService:
# #     return TagService(db)
#
#
# @pytest.fixture(scope="function")
# def tag(
#     tag_service: TagService, current_user_with_org: UserToken
# ) -> Generator[NewTagInput, None, None]:
#     new_tag_input = NewTagInput(
#         name=f"TEST_TAG_{datetime.now()}", hex_color="#FFFFFF", type="tag"
#     )
#     tag = tag_service.create_tag(current_user_with_org, new_tag_input)
#
#     try:
#         yield tag
#     finally:
#         tag_service.delete_tag(current_user_with_org, tag.id)
#
#
# @pytest.fixture(scope="function")
# def delete_tag(tag_service: TagService, current_user_with_org: UserToken) -> Tag:
#     new_tag_input = NewTagInput(
#         name=f"TEST_TAG_{datetime.now()}", hex_color="#FFFFFF", type="tag"
#     )
#     tag = tag_service.create_tag(current_user_with_org, new_tag_input)
#     return tag
#
#
# def test_create_tag(db: Session, current_user_with_org: UserToken) -> None:
#     tag_service = TagService(db)
#     new_tag_input = NewTagInput(
#         name=f"TEST_TAG_{datetime.now()}", hex_color="#FFFFFF", type="tag"
#     )
#     new_tag = tag_service.create_tag(current_user_with_org, new_tag_input)
#     assert new_tag is not None
#     assert new_tag.name == new_tag_input.name
#     assert new_tag.hex_color == new_tag_input.hex_color
#     assert new_tag.type == new_tag_input.type
#     assert new_tag.organization_id == current_user_with_org.organization_id
#     assert new_tag.created_by == current_user_with_org.user_id
#
#
# def test_create_existing_tag(
#     tag_service: TagService, tag: NewTagInput, current_user_with_org: UserToken
# ) -> None:
#     with pytest.raises(HTTPException):
#         tag_service.create_tag(
#             current_user_with_org, NewTagInput(**tag.model_dump(exclude_unset=True))
#         )
#
#
# def test_invalid_tag_update(
#     tag_service: TagService, tag: NewTagInput, current_user_with_org: UserToken
# ) -> None:
#     new_name = "UPDATED_TAG"
#     new_hex_color = "#000000."
#     new_type = "category"
#     with pytest.raises(ValidationError):
#         EditTagInput(name=new_name, hex_color=new_hex_color, type=new_type)
#
#
# def test_update_tag(
#     tag_service: TagService, tag: NewTagInput, current_user_with_org: UserToken
# ) -> None:
#     new_name = f"UPDATED_TAG_{datetime.now()}"
#     new_hex_color = "#000000"
#     edit_tag_input = EditTagInput(name=new_name, hex_color=new_hex_color)
#     updated_tag = tag_service.edit_tag(
#         current_user_with_org, str(tag.id), edit_tag_input
#     )
#     assert updated_tag is not None
#     assert updated_tag.name == new_name
#     assert updated_tag.hex_color == new_hex_color
#
#
# def test_list_tags_from_other_org(
#     tag_service: TagService, current_user_with_other_org: UserToken, tag: NewTagInput
# ) -> None:
#     lt_input = ListTagsInput(limit=10, offset=0, name=tag.name, type=tag.type)
#     tag_results = tag_service.list_tags(current_user_with_other_org, lt_input)
#     assert tag_results is not None
#     assert len(tag_results.results) == 0
#     assert tag_results.count == 0
#
#
# def test_associate_tag_from_other_org(
#     tag_service: TagService,
#     current_user_with_other_org: UserToken,
#     tag: NewTagInput,
#     content: DerivedContent,
# ) -> None:
#     content_id = content.id
#     tag_id = tag.id
#     include = True
#     with pytest.raises(HTTPException):
#         tag_service.associate_tag(
#             current_user_with_other_org.organization_id, content_id, tag_id, include
#         )
#
#
# def test_associate_tag_content_from_other_org(
#     tag_service: TagService,
#     current_user_with_org: UserToken,
#     tag: NewTagInput,
#     org_b_content: DerivedContent,
# ) -> None:
#     content_id = org_b_content.id
#     tag_id = tag.id
#     include = True
#     with pytest.raises(HTTPException):
#         tag_service.associate_tag(
#             current_user_with_org.organization_id, content_id, tag_id, include
#         )
#
#
# def test_list_tag_contents(
#     tag_service: TagService,
#     current_user_with_org: UserToken,
#     tag: NewTagInput,
#     content: DerivedContent,
# ) -> None:
#     lt_input = ListContentInput(limit=10, offset=0, latest_version_only=False)
#     results = tag_service.list_tag_contents(
#         current_user_with_org, str(tag.id), lt_input
#     )
#     assert results is not None
#     assert results.limit == lt_input.limit
#     assert results.offset == lt_input.offset
#
#
# def test_delete_tag(
#     tag_service: TagService,
#     current_user_with_org: UserToken,
#     delete_tag: Tag,
# ) -> None:
#     tag_service.delete_tag(
#         current_user_with_org, delete_tag.id
#     )  # if no exception is raised, the test passes
#
#
# def test_delete_tag_from_other_org(
#     tag_service: TagService,
#     current_user_with_other_org: UserToken,
#     delete_tag: Tag,
# ) -> None:
#     with pytest.raises(HTTPException):
#         tag_service.delete_tag(current_user_with_other_org, delete_tag.id)
