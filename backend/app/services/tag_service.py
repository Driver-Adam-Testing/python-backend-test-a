import logging
from uuid import UUID

from database.models_v1 import (
    DerivedContent,
    DocumentSource,
    Tag,
    TagContent,
    Workspace,
)
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.api.auth import CurrentUser
from app.repositories.base_repository import BaseRepository
from app.repositories.derived_content_type_repository import (
    DerivedContentTypeRepository,
)
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
                Workspace.organization_id
                == organization_id,  # get by workspace organization_id
            ],
            [Workspace],
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

        if (
            tag.type == "collection"
            and content.content_type.type_name
            not in DerivedContentTypeRepository.valid_collection_type_names()
        ):
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

        content.tag_links.append(
            TagContent(tag_id=tag.id, content_id=content.id, include=include_tag)
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

    def associate_collection_with_content(
        self: "TagService",
        organization_id: str,
        content_id: UUID,
        tag_id: UUID,
    ) -> TagAssociationResponse:
        logger.info(
            f"Associating collection tag {tag_id} with content {content_id} for organization {organization_id}"
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

        document = self.content_repository.get(content_id)

        if not document or document.workspace.organization_id != organization_id:
            logger.error(
                f"Content {content_id} not found for organization {organization_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Content not found"
            )

        tag_contents = self.session.exec(
            select(TagContent).where(TagContent.tag_id == tag_id)
        ).all()

        sources = [
            DocumentSource(
                document_id=content_id,
                source_id=tag_content.content_id,
                include=tag_content.include,
            )
            for tag_content in tag_contents
        ]

        for source in sources:
            self.session.merge(source)

        try:
            self.session.commit()
            logger.info(
                f"Collection tag {tag_id} associated with content {content_id} successfully"
            )
        except IntegrityError:
            self.session.rollback()
            logger.error(
                f"Integrity error while associating collection tag {tag_id} with content {content_id}"
            )

        return TagAssociationResponse(
            tag_id=tag_id,
            content_id=content_id,
            message="Collection associated successfully",
        )

    def create_tag(self: "TagService", user: CurrentUser, lt_input: NewTagInput) -> Tag:
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

    def disassociate_tag(
        self: "TagService",
        organization_id: str,
        content_id: UUID,
        tag_id: UUID,
    ) -> TagAssociationResponse:
        logger.info(
            f"Disassociating tag {tag_id} from content {content_id} for organization {organization_id}"
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

        content = self.content_repository.get(content_id)

        if not content or content.workspace.organization_id != organization_id:
            logger.error(
                f"Content {content_id} not found for organization {organization_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Content not found"
            )

        link = self.session.exec(
            select(TagContent)
            .where(TagContent.tag_id == tag_id)
            .where(TagContent.content_id == content_id)
        ).first()

        if link is None:
            logger.error(
                f"Tag association not found for tag {tag_id} and content {content_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tag association not found",
            )
        try:
            self.session.delete(link)
            self.session.commit()
            logger.info(
                f"Tag {tag_id} disassociated from content {content_id} successfully"
            )
            return TagAssociationResponse(
                tag_id=tag_id,
                content_id=content_id,
                message="Tag disassociated successfully",
            )
        except Exception as e:
            self.session.rollback()
            logger.error(
                f"Error disassociating tag {tag_id} from content {content_id}: {e}"
            )
            raise HTTPException(status_code=500, detail="Internal server error.")

    def edit_tag(
        self: "TagService", user: CurrentUser, tag_id: str, lt_input: EditTagInput
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
        self: "TagService", user: CurrentUser, lt_input: ListTagsInput
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
        self: "TagService", user: CurrentUser, tag_id: str, lt_input: ListContentInput
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

        content = self.content_service.get_list_content(
            user.organization_id,
            search_input=ListContentInput(
                limit=lt_input.limit,
                offset=lt_input.offset,
                text=lt_input.text,
                content_type_id=lt_input.content_type_id,
                content_type_name=lt_input.content_type_name,
                sort_by=lt_input.sort_by,
                sort_direction=lt_input.sort_direction,
                status=lt_input.status,
                tag_ids=[tag_id],
            ),
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

    def delete_tag(self: "TagService", user: CurrentUser, tag_id: UUID) -> bool:
        organization_id = user.organization_id

        tag = self.tag_repository.get(tag_id)
        if tag is None or tag.organization_id != organization_id:
            logger.error(f"Tag {tag_id} not found for user {user.user_id}")
            raise HTTPException(status_code=404, detail="Tag not found")

        if tag.content_links:
            logger.error(
                f"Tag {tag_id} has associated content. Disassociate content before deleting"
            )
            raise HTTPException(
                status_code=400,
                detail="Tag has associated content. Disassociate content before deleting",
            )

        try:
            self.tag_repository.delete(tag_id)
            self.session.commit()
            logger.info(f"Tag {tag_id} deleted for user {user.user_id}")
            return True
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error deleting tag {tag_id} for user {user.user_id}: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
