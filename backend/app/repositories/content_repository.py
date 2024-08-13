# import json
# from datetime import datetime
# from typing import Sequence, Optional
#
# from app.repositories.base_repository import BaseRepository
# from app.schemas.content_schema import ListContentInput, ListContentResults, ListContentResult
# from sqlmodel import Session, asc, desc, or_, select, func
#
# from sqlalchemy.exc import NoResultFound
# from database.models_v1 import (
#     DerivedContent,
#     DerivedContentType,
#     Workspace,
#     Enum_Derived_Content_Status,
#     Tag,
#     TagContent
# )
#
#
# # class WorkspaceRepository(BaseRepository[Workspace]):
# #     def __init__(self, session: Session):
# #         super().__init__(session, Workspace)
#
#
#
#
# class ContentRepository(BaseRepository[DerivedContent]):
#     def __init__(self, session: Session):
#         super().__init__(session, DerivedContent)
#         # self.session = session
#         self.derived_content_type_repository = DerivedContentTypeRepository(session)
#         self.workspace_repository = WorkspaceRepository(session)
#
#
#
#
