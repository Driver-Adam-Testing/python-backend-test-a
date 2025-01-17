# """
# DO NOT USE try-except in tests because it masks bugs.
# try:
# except HTTPException as e:
# Author: eric.miller@driverai.com
# """

# import contextlib
# from collections.abc import Generator
# from datetime import datetime
# from uuid import uuid4

# import pytest
# from database.models_v1 import (
#     ChunkAndEmbedding,
#     DerivedContent,
# )
# from fastapi import HTTPException
# from sqlmodel import Session

# from app.api.auth import UserToken
# from app.schemas.content_schema import (
#     ContentSourceAssociationItem,
#     CreateContentRequest,
#     ListContentInput,
#     ListContentTypesInput,
# )
# from app.schemas.tag_schema import NewTagInput
# from app.services.content_service import ContentService
# from app.services.tag_service import TagService


# @pytest.fixture
# def content_service(db: Session) -> ContentService:
#     return ContentService(db)


# @pytest.fixture
# def tag_service(db: Session) -> TagService:
#     return TagService(db)


# @pytest.fixture(scope="function")
# def content(
#     content_service: ContentService,
#     current_user_with_org: UserToken,
#     codebase_content: DerivedContent,
# ) -> Generator[DerivedContent, None, None]:
#     organization_id = current_user_with_org.organization_id
#     content = content_service.create_content(
#         organization_id, CreateContentRequest(content_type="application_note")
#     )
#     yield content

#     # Cleanup
#     content_service.content_repository.session.rollback()  # Ensure rollback before delete
#     content_service.content_repository.delete(content.id)


# @pytest.fixture(scope="function")
# def chunk_and_embed(
#     content_service: ContentService, delete_content: DerivedContent
# ) -> ChunkAndEmbedding:
#     chunk_and_embed = ChunkAndEmbedding(
#         content_id=delete_content.id,
#         text="TEST_CHUNK_AND_EMBED",
#         chunk_number=1,
#         created_at=datetime.now(),
#         updated_at=datetime.now(),
#     )
#     content_service.session.add(chunk_and_embed)
#     content_service.session.commit()
#     return chunk_and_embed


# @pytest.fixture(scope="function")
# def related_entities(
#     content_service: ContentService,
#     tag_service: TagService,
#     current_user_with_org: UserToken,
#     content: DerivedContent,
#     delete_content: DerivedContent,
#     tag: NewTagInput,
#     chunk_and_embed: ChunkAndEmbedding,
#     other_content: DerivedContent,
# ) -> list:
#     # Associate content with delete_content
#     content_source_associations = [
#         ContentSourceAssociationItem(source_content_id=delete_content.id, include=True)
#     ]
#     # Associate source content with content
#     content_service.associate_sources_with_content(
#         current_user_with_org.organization_id, content.id, content_source_associations
#     )
#     other_content_source_associations = [
#         ContentSourceAssociationItem(source_content_id=other_content.id, include=True)
#     ]
#     # Associate source content with delete_content
#     content_service.associate_sources_with_content(
#         current_user_with_org.organization_id,
#         delete_content.id,
#         other_content_source_associations,
#     )
#     # Associate tag with delete_content
#     tag_service.associate_tag(
#         current_user_with_org.organization_id, delete_content.id, tag.id
#     )

#     return [delete_content, content, tag, chunk_and_embed]


# @pytest.fixture(scope="function")
# def tag(
#     tag_service: TagService, current_user_with_org: UserToken
# ) -> Generator[NewTagInput, None, None]:
#     new_tag_input = NewTagInput(
#         name=f"TEST_TAG_{datetime.now()}", hex_color="#FFFFFF", type="tag"
#     )
#     tag = tag_service.create_tag(current_user_with_org, new_tag_input)

#     try:
#         yield tag
#     finally:
#         tag_service.delete_tag(current_user_with_org, tag.id)


# def test_create_application_note(
#     content_service: ContentService, current_user_with_org: UserToken
# ) -> None:
#     organization_id = current_user_with_org.organization_id
#     new_content = content_service.create_content(
#         organization_id, CreateContentRequest(content_type="application_note")
#     )
#     assert new_content is not None
#     assert new_content.content_type.type_name == "application_note"


# def test_create_application_note_no_default_workspace(
#     content_service: ContentService, current_user_with_other_org: UserToken
# ) -> None:
#     """
#     by default, the default workspace is created for an organization when finding the default workspace
#     """
#     organization_id = current_user_with_other_org.organization_id
#     content = content_service.create_content(
#         organization_id, CreateContentRequest(content_type="application_note")
#     )
#     assert content is not None
#     content_service.content_repository.delete(content.id)


# def test_create_other_content_type(
#     content_service: ContentService, current_user_with_org: UserToken
# ) -> None:
#     organization_id = current_user_with_org.organization_id
#     with pytest.raises(HTTPException):
#         content_service.create_content(
#             organization_id, CreateContentRequest(content_type="symbol")
#         )


# def test_get_list_content(
#     content_service: ContentService,
#     current_user_with_org: UserToken,
#     content: DerivedContent,
# ) -> None:
#     lc_input = ListContentInput(limit=10, offset=0, latest_version_only=False)
#     results = content_service.get_list_content(
#         current_user_with_org.organization_id, lc_input
#     )
#     assert results is not None
#     assert results.limit == lc_input.limit
#     assert results.offset == lc_input.offset


# def test_get_list_content_from_other_org(
#     content_service: ContentService,
#     current_user_with_other_org: UserToken,
#     content: DerivedContent,
# ) -> None:
#     lc_input = ListContentInput(
#         limit=10, offset=0, text="TEST", latest_version_only=False
#     )
#     results = content_service.get_list_content(
#         current_user_with_other_org.organization_id, lc_input
#     )
#     assert results is not None
#     assert len(results.results) == 0
#     assert results.count == 0


# def test_get_list_content_types(content_service: ContentService) -> None:
#     lct_input = ListContentTypesInput(limit=10, offset=0)
#     results = content_service.get_list_content_types(lct_input)
#     assert results is not None
#     assert len(results.results) > 0


# def test_get_content_sources(
#     content_service: ContentService,
#     current_user_with_org: UserToken,
#     content: DerivedContent,
# ) -> None:
#     response = content_service.get_content_sources(
#         content.id, current_user_with_org.organization_id
#     )
#     assert response is not None
#     assert response.results is not None


# def test_get_content_sources_from_other_org(
#     content_service: ContentService,
#     current_user_with_other_org: UserToken,
#     content: DerivedContent,
# ) -> None:
#     with pytest.raises(HTTPException):
#         content_service.get_content_sources(
#             content.id, current_user_with_other_org.organization_id
#         )


# def test_get_content_by_id(
#     content_service: ContentService,
#     current_user_with_org: UserToken,
#     content: DerivedContent,
# ) -> None:
#     fetched_content = content_service.get_content_by_id(
#         content.id, current_user_with_org.organization_id
#     )
#     assert fetched_content is not None
#     assert fetched_content.id == content.id


# def test_get_content_by_id_from_other_org(
#     content_service: ContentService,
#     current_user_with_other_org: UserToken,
#     content: DerivedContent,
# ) -> None:
#     with pytest.raises(HTTPException):
#         content_service.get_content_by_id(
#             content.id, current_user_with_other_org.organization_id
#         )


# def test_get_content_root_by_id_from_other_org(
#     content_service: ContentService,
#     current_user_with_other_org: UserToken,
#     content: DerivedContent,
# ) -> None:
#     with pytest.raises(HTTPException):
#         content_service.get_content_root_by_id(
#             content.id, current_user_with_other_org.organization_id
#         )


# def test_associate_sources_with_content(
#     content_service: ContentService,
#     current_user_with_org: UserToken,
#     content: DerivedContent,
#     source_content: DerivedContent,
# ) -> None:
#     content_id = content.id
#     source_content_id = source_content.id
#     content_source_associations = [
#         ContentSourceAssociationItem(source_content_id=source_content_id, include=True)
#     ]
#     response = content_service.associate_sources_with_content(
#         current_user_with_org.organization_id, content_id, content_source_associations
#     )
#     assert response is not None
#     assert response.content_id == content_id
#     assert len(response.sources) == 1
#     assert response.sources[0].source_content_id == source_content_id

#     content_service.disassociate_document_source(
#         current_user_with_org.organization_id, content_id, source_content_id
#     )


# def test_associate_sources_with_content_from_other_org(
#     content_service: ContentService,
#     current_user_with_other_org: UserToken,
#     content: DerivedContent,
#     source_content: DerivedContent,
# ) -> None:
#     content_id = content.id
#     source_content_id = source_content.id
#     content_source_associations = [
#         ContentSourceAssociationItem(source_content_id=source_content_id, include=True)
#     ]
#     with pytest.raises(HTTPException):
#         content_service.associate_sources_with_content(
#             current_user_with_other_org.organization_id,
#             content_id,
#             content_source_associations,
#         )


# def test_associate_invalid_sources_with_content(
#     content_service: ContentService,
#     current_user_with_org: UserToken,
#     content: DerivedContent,
# ) -> None:
#     content_id = content.id
#     source_content_id = uuid4()
#     content_source_associations = [
#         ContentSourceAssociationItem(source_content_id=source_content_id, include=True)
#     ]
#     with pytest.raises(HTTPException):
#         content_service.associate_sources_with_content(
#             current_user_with_org.organization_id,
#             content_id,
#             content_source_associations,
#         )


# def test_disassociate_document_source(
#     content_service: ContentService,
#     current_user_with_org: UserToken,
#     content: DerivedContent,
#     source_content: DerivedContent,
# ) -> None:
#     content_id = content.id
#     source_content_id = source_content.id
#     content_service.associate_sources_with_content(
#         current_user_with_org.organization_id,
#         content_id,
#         [
#             ContentSourceAssociationItem(
#                 source_content_id=source_content_id, include=True
#             )
#         ],
#     )

#     response = content_service.disassociate_document_source(
#         current_user_with_org.organization_id, content_id, source_content_id
#     )
#     assert response is not None
#     assert response.document_id == content_id
#     assert response.source_id == source_content_id


# def test_disassociate_document_source_from_other_org(
#     content_service: ContentService,
#     current_user_with_org: UserToken,
#     content: DerivedContent,
#     source_content: DerivedContent,
# ) -> None:
#     content_id = content.id
#     source_content_id = source_content.id
#     content_service.associate_sources_with_content(
#         current_user_with_org.organization_id,
#         content_id,
#         [
#             ContentSourceAssociationItem(
#                 source_content_id=source_content_id, include=True
#             )
#         ],
#     )

#     try:
#         with pytest.raises(HTTPException):
#             content_service.disassociate_document_source(
#                 "some_other_org", content_id, source_content_id
#             )
#         response = content_service.disassociate_document_source(
#             current_user_with_org.organization_id, content_id, source_content_id
#         )
#         assert response is not None
#         assert response.document_id == content_id
#         assert response.source_id == source_content_id
#     finally:
#         # Cleanup
#         with contextlib.suppress(
#             HTTPException
#         ):  # this is to prevent the test from failing if the cleanup already happened
#             content_service.disassociate_document_source(
#                 current_user_with_org.organization_id, content_id, source_content_id
#             )


# def test_edit_content(
#     content_service: ContentService,
#     current_user_with_org: UserToken,
#     content: DerivedContent,
# ) -> None:
#     organization_id = current_user_with_org.organization_id
#     content_id = content.id
#     new_content = {
#         "content_name": "Updated Content Name",
#         "content": "Updated content",
#         "misc_metadata": {"key": "value"},
#     }

#     updated_content = content_service.edit_content(
#         organization_id, content_id, new_content
#     )

#     assert updated_content is not None
#     assert updated_content.id == content_id
#     assert updated_content.content_name == "Updated Content Name"
#     assert updated_content.content == "Updated content"
#     assert updated_content.misc_metadata == {"key": "value"}


# def test_edit_content_from_other_org(
#     content_service: ContentService,
#     current_user_with_other_org: UserToken,
#     content: DerivedContent,
# ) -> None:
#     organization_id = current_user_with_other_org.organization_id
#     content_id = content.id
#     new_content = {
#         "content_name": "Updated Content Name",
#         "content": "Updated content",
#         "misc_metadata": {"key": "value"},
#     }
#     with pytest.raises(HTTPException):
#         content_service.edit_content(organization_id, content_id, new_content)


# def test_delete_content(
#     content_service: ContentService,
#     current_user_with_org: UserToken,
#     delete_content: DerivedContent,
#     related_entities: list,
# ) -> None:
#     """
#     Test that content can be deleted
#     related_entities: creates  source_content, tag, chunk_and_embed
#     """
#     organization_id = current_user_with_org.organization_id
#     content_id = delete_content.id

#     # Ensure the content exists before deletion
#     fetched_content = content_service.get_content_by_id(content_id, organization_id)
#     assert fetched_content is not None

#     # Delete the content
#     content_service.delete_content(organization_id, content_id)

#     # Ensure the content no longer exists after deletion
#     with pytest.raises(
#         HTTPException
#     ):  # Replace with the actual exception your service raises
#         content_service.get_content_by_id(content_id, organization_id)


# def test_delete_content_from_other_org(
#     content_service: ContentService,
#     current_user_with_org: UserToken,
#     delete_content: DerivedContent,
#     related_entities: list,
# ) -> None:
#     """
#     Test that content can be deleted
#     related_entities: creates  source_content, tag, chunk_and_embed
#     """
#     organization_id = current_user_with_org.organization_id
#     content_id = delete_content.id

#     try:
#         with pytest.raises(HTTPException):
#             content_service.delete_content("some_other_org", content_id)
#     finally:
#         content_service.delete_content(organization_id, content_id)

#     # Ensure the content no longer exists after deletion
#     with pytest.raises(
#         HTTPException
#     ):  # Replace with the actual exception your service raises
#         content_service.get_content_by_id(content_id, organization_id)


# def test_delete_codebase(
#     content_service: ContentService,
#     current_user_with_org: UserToken,
#     complete_codebase_with_related_entities: DerivedContent,
# ) -> None:
#     organization_id = current_user_with_org.organization_id
#     content_id = complete_codebase_with_related_entities.id
#     content_service.delete_content(organization_id, content_id)


# def test_delete_codebase_from_other_org(
#     content_service: ContentService,
#     current_user_with_org: UserToken,
#     complete_codebase_with_related_entities: DerivedContent,
# ) -> None:
#     organization_id = current_user_with_org.organization_id
#     content_id = complete_codebase_with_related_entities.id
#     with pytest.raises(HTTPException):
#         content_service.delete_content("some_other_org", content_id)

#     content_service.delete_content(organization_id, content_id)
