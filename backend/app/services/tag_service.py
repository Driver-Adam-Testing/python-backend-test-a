import logging
from fastapi import HTTPException

from sqlmodel import Session, asc, desc, or_, select, func, text

from app.repositories.base_repository import BaseRepository

from app.api.auth import CurrentUser

from app.schemas.tag_schema import (
    ListTagsInput,
    ListTagsResults,
    NewTagInput,
    EditTagInput,
    ListTagContentsResults
)

from app.schemas.content_schema import ListContentInput

from app.api.session import CurrentSession
from database.models_v1 import Tag

logger = logging.getLogger(__name__)


class TagService:
    def __init__(self, session: Session):
        self.session = session
        self.tag_repository = BaseRepository(session, Tag)

    def list_tags(self, user: CurrentUser, lt_input: ListTagsInput) -> ListTagsResults:

        statement = [user.organization_id == Tag.organization_id]
        count_by = [user.organization_id == Tag.organization_id]

        if lt_input.name:
            statement.append(Tag.name.contains(lt_input.name))
            count_by.append(Tag.name.contains(lt_input.name))

        total_count = self.tag_repository.count_by(count_by)
        results = self.tag_repository.get_all(
            lt_input.limit,
            lt_input.offset,
            conditions=statement,
        )
        return ListTagsResults(
            results=results,
            offset=lt_input.offset,
            limit=lt_input.limit,
            count=total_count
        )

    def create_tag(self, user: CurrentUser, lt_input: NewTagInput) -> Tag:

        return self.tag_repository.create(Tag(
            **lt_input.model_dump(exclude_unset=True),
            organization_id=user.organization_id,
            created_by=user.user_id,
            updated_by=user.user_id,
        ))

    def edit_tag(self, user: CurrentUser, tag_id: str, et_input: EditTagInput) -> Tag:

        tag = self.tag_repository.get_by_conditions([Tag.id == tag_id and Tag.organization_id == user.organization_id])

        if tag:
            tag_updates = et_input.model_dump(exclude_unset=True)
            tag = self.tag_repository.update(tag, Tag(**tag_updates, updated_by=user.user_id))
            return tag
        logger.error("Tag not found to edit")
        raise HTTPException(status_code=404, detail="Tag not found")

# def list_tag_contents(self, user: CurrentUser, tag_id: str, input: ListContentInput) -> ListTagContentsResults:
#     tag = self.session.exec(
#         select(Tag).where(
#             Tag.id == tag_id and Tag.organization_id == user.organization_id
#         )
#     ).first()
#     if tag:
#         content = list_content(
#             session,
#             user,
#             input=ListContentInput(
#                 limit=input.limit,
#                 offset=input.offset,
#                 text=input.text,
#                 content_type_id=input.content_type_id,
#                 content_type_name=input.content_type_name,
#                 sort_by=input.sort_by,
#                 sort_direction=input.sort_direction,
#                 status=input.status,
#                 tag_ids=[tag_id],
#             ),
#         )
#         return ListTagContentsResults(
#             tag=tag,
#             results=content.results,
#             offset=input.offset,
#             limit=input.limit,
#             count=content.count,
#         )
#     logger.error("Tag not found.")
#     raise HTTPException(status_code=404, detail="Tag not found")


def get_tag_service(session: CurrentSession) -> TagService:
    return TagService(session=session)
