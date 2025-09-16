from app.core.logger import logger
from app.repositories.base_repository import BaseRepository
from database.models import GithubAppInstallation
from sqlalchemy import func
from sqlmodel import Session, col, select


class GithubAppInstallationsRepository(BaseRepository[GithubAppInstallation]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, GithubAppInstallation)

    def list_by_organization_id(
        self, organization_id: str
    ) -> list[GithubAppInstallation]:
        logger.debug(f"Fetching GithubAppInstallations for: {organization_id}")
        return self.session.exec(
            select(GithubAppInstallation).where(
                GithubAppInstallation.organization_id == organization_id
            )
        ).all()

    def list_by_installation_id(
        self, installation_id: str
    ) -> list[GithubAppInstallation]:
        logger.debug(f"Fetching GithubAppInstallations for: {installation_id}")
        return self.session.exec(
            select(GithubAppInstallation).where(
                GithubAppInstallation.github_app_installation_id == installation_id
            )
        ).all()

    def exists(self, organization_id: str, installation_id: str) -> bool:
        logger.info(
            f"Checking if GH app installation ID = {installation_id} already exists in {organization_id}"
        )
        count = self.session.exec(
            select(func.count(col(GithubAppInstallation.id))).where(
                GithubAppInstallation.github_app_installation_id
                == str(installation_id),
                GithubAppInstallation.organization_id == organization_id,
            )
        ).one()
        return count > 0
