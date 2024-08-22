from sqlalchemy.orm import Session
from app.repositories.base_repository import BaseRepository
from database.models_v1 import TagContent
from app.schemas.tag_contents_schema import TagContentCreate
from fastapi import HTTPException, status


class TagContentService:
    def __init__(self, session: Session):
        self.session = session
        self.tag_content_repository = BaseRepository(session, TagContent)

    def get_tag_content(self, tag_id: str, content_id: str) -> TagContent | None:
       return  self.tag_content_repository.get_by_pk(tag_id=tag_id, content_id=content_id)
        
    
    def create_tag_content(self, tag_content: TagContentCreate):
        tag_content_data = tag_content.model_dump()
        tag_id = tag_content_data['tag_id']
        content_id = tag_content_data['content_id']
        
        # Check if the tag_content already exists
        existing_tag_content = self.get_tag_content(tag_id, content_id)
        if existing_tag_content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"TagContent with tag_id {tag_id} and content_id {content_id} already exists."
            )

        tag_content_instance = TagContent(**tag_content_data)
        return self.tag_content_repository.create(tag_content_instance)
    
    def delete_tag_content(self, tag_id: str, content_id: str):
        return self.tag_content_repository.delete_by_pk(tag_id=tag_id, content_id=content_id)