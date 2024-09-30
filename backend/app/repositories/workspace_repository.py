from app.core.logger import logger
from app.repositories.base_repository import BaseRepository
from database.models_v1 import Workspace
from sqlmodel import Session


class WorkspaceRepository(BaseRepository[Workspace]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, Workspace)

    def get_default_workspace(self, organization_id: str) -> Workspace:
        logger.info(
            f"Fetching default workspace for organization_id: {organization_id}"
        )
        default_workspace = self.get_by_conditions(
            [
                Workspace.organization_id == organization_id,
                Workspace.display_name == "Default",
            ]
        )
        if default_workspace is None:
            logger.info("Creating Default workspace...")
            default_workspace = Workspace(
                organization_id=organization_id,
                display_name="Default",
                description="Default",
            )
            default_workspace = self.create(default_workspace)

        return default_workspace
