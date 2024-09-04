from database.models_v1 import Workspace
from sqlmodel import Session

from app.core.logger import logger
from app.repositories.base_repository import BaseRepository


class WorkspaceRepository(BaseRepository[Workspace]):
    def __init__(self, session: Session):
        super().__init__(session, Workspace)

    def get_default_workspace(self, organization_id: str) -> Workspace | None:
        logger.info(
            f"Fetching default workspace for organization_id: {organization_id}"
        )
        default_workspace = self.get_by_conditions(
            [
                Workspace.organization_id == organization_id,
                Workspace.display_name == "Default",
            ]
        )
        return default_workspace
