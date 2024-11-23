import logging

from app.repositories.base_repository import BaseRepository
from database.models_v1 import User
from sqlmodel import Session

logger = logging.getLogger(__name__)


class UserRepository(BaseRepository[User]):
    def __init__(self, session: Session):
        super().__init__(session, User)

    def get_by_user_and_org(self, user_id: str, organization_id: str) -> User | None:
        logger.debug(
            f"Fetching user by user_id: {user_id} and organization_id: {organization_id}"
        )
        conditions = [
            User.user_id == user_id,
            User.organization_id == organization_id,
        ]
        return self.get_by_conditions(conditions)

    def create_or_update(
        self, user_id: str, organization_id: str, github_app_installation_id: str | None
    ) -> User:
        try:
            user = self.get_by_user_and_org(user_id, organization_id)
            if user:
                user.github_app_installation_id = github_app_installation_id
                self.session.add(user)
                self.session.commit()
                self.session.refresh(user)
            else:
                user = User(
                    user_id=user_id,
                    organization_id=organization_id,
                    github_app_installation_id=github_app_installation_id,
                )
                self.create(user)
            return user
        except Exception as e:
            logger.error(
                f"Error while creating/updating user. "
                f"user_id={user_id}, organization_id={organization_id}, error={e}"
            )
            raise e
