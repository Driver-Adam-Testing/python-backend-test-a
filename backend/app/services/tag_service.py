import logging
from uuid import UUID

from database.models_v1 import (
    DerivedContent,
    Tag,
)
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

from app.api.auth import UserToken
from app.repositories.base_repository import BaseRepository
from app.schemas.content_schema import ListContentInput, TagAssociationResponse
from app.schemas.tag_schema import (
    EditTagInput,
    ListTagContentsResults,
    ListTagsInput,
    ListTagsResults,
    NewTagInput,
)
from app.services.content_service import ContentService

logger = logging.getLogger(__name__)


class TagService:
    def __init__(self: "TagService", session: Session) -> None:
        self.session = session
        self.tag_repository = BaseRepository(session, Tag)
        self.content_repository = BaseRepository(session, DerivedContent)
        self.content_service = ContentService(session)

    def associate_tag(
        self: "TagService",
        organization_id: str,
        content_id: UUID,
        tag_id: UUID,
        include_tag: bool = True,
    ) -> TagAssociationResponse:
        logger.info(
            f"Associating tag {tag_id} with content {content_id} for organization {organization_id}"
        )

        content = self.content_repository.get_by_conditions(
            [
                DerivedContent.id == content_id,
            ],
            [],
        )

        if not content:
            logger.error(
                f"Content {content_id} not found for organization {organization_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Content not found.",
            )

        tag = self.tag_repository.get_by_conditions(
            [
                Tag.id == tag_id,
                Tag.organization_id == organization_id,  # get by organization_id
            ]
        )

        if not tag:
            logger.error(f"Tag {tag_id} not found for organization {organization_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found"
            )

        if tag.type == "collection":
            logger.error(
                f"Invalid content type for collection tag {tag_id} and content {content_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Collections can only be associated with codebases, directories, files or pdfs.",
            )

        include_tag = (
            include_tag
            if include_tag is not None and tag.type == "collection"
            else True
        )

        try:
            self.session.commit()
            logger.info(
                f"Tag {tag_id} associated with content {content_id} successfully"
            )
        except IntegrityError:
            self.session.rollback()
            logger.error(
                f"Integrity error while associating tag {tag_id} with content {content_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tag association already exists",
            )

        return TagAssociationResponse(
            tag_id=tag_id,
            content_id=content_id,
            message=f"{tag.type} associated successfully",
        )

    def create_tag(self: "TagService", user: UserToken, lt_input: NewTagInput) -> Tag:
        try:
            return self.tag_repository.create(
                Tag(
                    name=lt_input.name.strip(),
                    hex_color=lt_input.hex_color.strip(),
                    type=lt_input.type,
                    organization_id=user.organization_id,
                    created_by=user.user_id,
                    updated_by=user.user_id,
                )
            )
        except IntegrityError as e:
            self.session.rollback()  # Rollback the session to clear the failed transaction
            if "duplicate key value violates unique constraint" in str(e.orig):
                logging.error("Tag name already exists")
                raise HTTPException(status_code=400, detail="Tag name already exists.")
            else:
                logging.error(f"Unexpected error: {e}")
                raise HTTPException(status_code=500, detail="Internal server error.")

    def edit_tag(
        self: "TagService", user: UserToken, tag_id: str, lt_input: EditTagInput
    ) -> Tag:
        tag = self.tag_repository.get_by_conditions(
            [
                Tag.id == tag_id,
                Tag.organization_id == user.organization_id,  # get by organization_id
            ]
        )

        if not tag:
            logger.error(
                f"Tag {tag_id} not found for organization {user.organization_id}"
            )
            raise HTTPException(status_code=404, detail="Tag not found")
        try:
            tag_updates = lt_input.model_dump(exclude_unset=True)
            tag = self.tag_repository.update(
                tag, Tag(**tag_updates, updated_by=user.user_id)
            )

            logger.info(f"Tag {tag_id} updated for organization {user.organization_id}")
            return tag
        except Exception as e:
            self.session.rollback()  # Rollback the session on failure
            logger.error(
                f"Error updating tag {tag_id} for organization {user.organization_id}: {e}"
            )
            raise HTTPException(status_code=500, detail="Internal server error")

    def list_tags(
        self: "TagService", user: UserToken, lt_input: ListTagsInput
    ) -> ListTagsResults:
        logger.info(f"Listing tags for user {user.user_id} with input {lt_input}")
        statement = [user.organization_id == Tag.organization_id]
        count_by = [user.organization_id == Tag.organization_id]

        if lt_input.name:
            statement.append(Tag.name.contains(lt_input.name))
            count_by.append(Tag.name.contains(lt_input.name))

        if lt_input.type:
            statement.append(Tag.type == lt_input.type)
            count_by.append(Tag.type == lt_input.type)

        # total_count = self.session.exec(count_statement).one()
        total_count = self.tag_repository.count_by(count_by)
        results = self.tag_repository.get_all(
            lt_input.limit,
            lt_input.offset,
            conditions=statement,
        )
        logger.info(f"Found {total_count} tags for user {user.user_id}")
        return ListTagsResults(
            results=results,
            offset=lt_input.offset,
            limit=lt_input.limit,
            count=total_count,
        )

    def list_tag_contents(
        self: "TagService", user: UserToken, tag_id: str, lt_input: ListContentInput
    ) -> ListTagContentsResults:
        logger.info(
            f"Listing contents for tag {tag_id} for user {user.user_id} with input {lt_input}"
        )
        tag = self.tag_repository.get_by_conditions(
            [Tag.id == tag_id and Tag.organization_id == user.organization_id]
        )

        if tag is None:
            logger.error(f"Tag {tag_id} not found for user {user.user_id}")
            raise HTTPException(status_code=404, detail="Tag not found")

        lt_input.tag_ids = [tag_id]

        content = self.content_service.get_list_content(
            user.organization_id,
            search_input=lt_input,
        )
        logger.info(
            f"Found {content.count} contents for tag {tag_id} for user {user.user_id}"
        )
        return ListTagContentsResults(
            tag=tag,
            results=content.results,
            offset=lt_input.offset,
            limit=lt_input.limit,
            count=content.count,
        )

    def delete_tag(self: "TagService", user: UserToken, tag_id: UUID) -> None:
        organization_id = user.organization_id

        tag: Tag | None = self.tag_repository.get(tag_id)

        if tag is None or tag.organization_id != organization_id:
            logger.error(f"Tag {tag_id} not found for user {user.user_id}")
            raise HTTPException(status_code=404, detail="Tag not found")

        try:
            delete_tag_and_related_entities(self.session, tag)
            logger.info(f"Tag {tag_id} deleted by user {user.user_id}")
        except Exception as e:
            self.session.rollback()
            logger.exception(
                f"Error deleting tag {tag_id} for user {user.user_id}: {e}"
            )
            raise HTTPException(status_code=500, detail="Internal server error")


def delete_tag_and_related_entities(session: Session, tag: Tag) -> None:
    session.delete(tag)
    session.commit()
