import base64
import json
import logging
import secrets

from database.models_v1 import GitProviderApp, GitProviderAppInstallation
from shared.interfaces.aws_client_config import AWSClientConfig
from shared.secret_management.aws_secret_management import (
    AWSSecretManagementStrategy,
    format_secret_name,
)
from sqlmodel import Session

from app.git_providers.providers.gitlab_provider import (
    GitLabProvider,
    GitProviderAppRevokeError,
)
from app.git_providers.utils.errors import GitProviderAccessTokenError
from app.repositories.git_provider_repository import (
    delete_git_provider_app_install,
    git_provider_app_by_id,
    git_provider_app_installation_by_id,
    git_provider_app_installation_by_org_id,
    git_provider_app_installation_by_user_id,
    git_provider_apps_by_org_id,
)
from app.schemas.git_provider_schema import (
    CreateGitProviderAppRequest,
    GitProviderAppTokenSecret,
    GitRepository,
    GroupAccessToken,
)
from app.schemas.secret_management_schema import (
    APP_INSTALL_GAT_NAME_PREFIX,
    APP_INSTALL_SECRET_NAME_PREFIX,
)

logger = logging.getLogger(__name__)

# TODO:
def fetch_git_provider_apps_by_org_id(
    session: Session, organization_id: str
) -> list[GitProviderApp]:
    return git_provider_apps_by_org_id(session, organization_id)


def fetch_git_provider_app_install_by_user_id(
    session: Session, organization_id: str, user_id: str, app_id: str
) -> GitProviderAppInstallation | None:
    return git_provider_app_installation_by_user_id(
        session, organization_id, app_id, user_id
    )


def create_git_provider_app(
    session: Session,
    gp_app_input: CreateGitProviderAppRequest,
    aws_config: AWSClientConfig,
) -> GitProviderApp:
    git_provider_app = GitProviderApp(
        owner_organization_id=gp_app_input.organization_id,
        name=gp_app_input.name,
        provider_kind=gp_app_input.provider_kind,
        shared_provider=gp_app_input.shared_provider,
        base_url=gp_app_input.base_url,
    )
    session.add(git_provider_app)

    # Commit the session if secret writing was successful
    try:
        logger.info(f"App {git_provider_app.id} created successfully.")
        session.commit()
    except Exception as e:
        logger.error(
            f"Error committing session for app {git_provider_app.name} with ID {git_provider_app.id}. Rolling back database."
        )
        session.rollback()
        raise e

    session.refresh(git_provider_app)

    return git_provider_app


def install_group_access_token(
    session: Session,
    organization_id: str,
    app_id: str,
    gat: GroupAccessToken,
    aws_config: AWSClientConfig,
) -> GitProviderAppInstallation:
    is_token_valid = validate_group_access_token(
        session, organization_id, app_id, gat.token, aws_config
    )
    if not is_token_valid:
        raise GitProviderAccessTokenError("Invalid group access token")
    git_provider_app = git_provider_app_by_id(session, organization_id, app_id)

    secrets_manager = AWSSecretManagementStrategy(config=aws_config)
    app_install = GitProviderAppInstallation(
        organization_id=organization_id,
        misc_metadata={"kind": "group", "name": gat.name},
    )
    webhook_secret = secrets.token_urlsafe(32)
    # Attempt to write the secret
    app_secret_name = format_secret_name(
        APP_INSTALL_GAT_NAME_PREFIX, str(app_install.id)
    )
    # TODO: maybe make this 2 secrets, one for token and one for webhook secret
    secret_value = json.dumps(
        GitProviderAppTokenSecret(
            token=gat.token, secret_token=webhook_secret
        ).model_dump()
    )
    try:
        logger.info(f"Writing secret {app_secret_name}")
        secrets_manager.write_secret(app_secret_name, secret_value)

    except Exception as e:
        logger.error(
            f"Error writing secret for app {git_provider_app.name} with ID {git_provider_app.id}. Aborting operation."
        )
        session.rollback()
        raise e
    git_provider_app.app_installations.append(app_install)
    session.add(git_provider_app)

    # Commit the session if secret writing was successful
    try:
        session.commit()
        logger.info(f"App {git_provider_app.id} created successfully.")
    except Exception as e:
        logger.error(
            f"Error committing session for app {git_provider_app.name} with ID {git_provider_app.id}. Rolling back database."
        )
        secrets_manager.delete_secret(app_secret_name)
        session.rollback()
        raise e

    session.refresh(git_provider_app)

    return app_install


def update_group_access_token(
    session: Session,
    organization_id: str,
    app_id: str,
    installation_id: str,
    gat: GroupAccessToken,
    aws_config: AWSClientConfig,
) -> None:
    is_token_valid = validate_group_access_token(
        session, organization_id, app_id, gat.token, aws_config
    )
    if not is_token_valid:
        raise GitProviderAccessTokenError("Invalid group access token")

    app_install = git_provider_app_installation_by_id(session, installation_id)
    secrets_manager = AWSSecretManagementStrategy(config=aws_config)
    app_secret_name = format_secret_name(
        APP_INSTALL_GAT_NAME_PREFIX, str(app_install.id)
    )

    try:
        secret_dict = secrets_manager.read_secret(app_secret_name)
        app_token_secret = GitProviderAppTokenSecret(**secret_dict)
        app_token_secret.token = gat.token
        updated_secret_value = json.dumps(app_token_secret.model_dump())
        secrets_manager.write_secret(app_secret_name, updated_secret_value)
    except Exception as e:
        logger.exception(
            f"Error updating group access token secret for installation {app_install.id} owned by org {organization_id}. Aborting operation."
        )
        raise e


def authorize_git_provider(
    session: Session,
    organization_id: str,
    user_id: str,
    app_id: str,
    aws_config: AWSClientConfig,
) -> str:
    git_provider = GitLabProvider.from_config(
        git_provider_app_by_id(session, organization_id, app_id), aws_config
    )
    return git_provider.authorize_provider(organization_id, user_id, app_id)


def handle_authorization_callback(
    session: Session,
    code: str,
    state: str,
    aws_config: AWSClientConfig,
) -> None:
    state_bytes = base64.b64decode(state)
    state_str = state_bytes.decode("utf-8")
    state_dict = json.loads(state_str)

    organization_id, user_id, application_id = (
        state_dict["organization_id"],
        state_dict["user_id"],
        state_dict["application_id"],
    )

    git_provider_app = git_provider_app_by_id(session, organization_id, application_id)
    existing_app_install = next(
        (
            app_install
            for app_install in git_provider_app.app_installations
            if app_install.user_id == user_id
            and app_install.organization_id == organization_id
        ),
        None,
    )
    if existing_app_install is None:
        logger.info(
            f"App installation does not exist for user {user_id} and app {application_id}"
        )
        app_install = GitProviderAppInstallation(
            user_id=user_id, organization_id=organization_id
        )
        git_provider_app.app_installations.append(app_install)
        session.add(git_provider_app)
        session.commit()
        session.refresh(git_provider_app)
        app_install_id = app_install.id
        git_provider = GitLabProvider.from_config(git_provider_app, aws_config)
        git_provider.handle_app_authorization_callback(code, str(app_install_id))
    else:
        logger.info(
            f"App installation already exists for user {user_id} and app {application_id}"
        )


def fetch_user_repositories_by_app_id(
    session: Session,
    organization_id: str,
    user_id: str,
    app_id: str,
    aws_config: AWSClientConfig,
) -> list[GitRepository]:
    git_provider = GitLabProvider.from_config(
        git_provider_app_by_id(session, organization_id, app_id), aws_config
    )

    user_app_install = git_provider_app_installation_by_user_id(
        session, organization_id, app_id, user_id
    )
    try:
        return git_provider.fetch_repos(user_app_install)
    except GitProviderAppRevokeError as e:
        logger.error(
            f"Access token expired or was revoked for user {user_id} and app {app_id}"
        )
        # if we get an error fetching repositories, getting the access token failed and need to uninstall the app and force the user to re-authenticate/reinstall
        handle_user_app_revoke(
            session, organization_id, app_id, str(user_app_install.id), aws_config
        )
        raise e


def fetch_group_repositories_by_app_id(
    session: Session,
    organization_id: str,
    user_id: str,
    app_id: str,
    aws_config: AWSClientConfig,
) -> list[GitRepository]:
    git_provider = GitLabProvider.from_config(
        git_provider_app_by_id(session, organization_id, app_id), aws_config
    )

    group_app_installs = git_provider_app_installation_by_org_id(
        session, organization_id, app_id
    )
    repositories = []
    for group_app_install in group_app_installs:
        repositories.extend(git_provider.fetch_group_repos(group_app_install))

    return repositories


def fetch_group_repositories_by_installation_id(
    session: Session,
    organization_id: str,
    user_id: str,
    app_id: str,
    installation_id: str,
    aws_config: AWSClientConfig,
) -> list[GitRepository]:
    git_provider = GitLabProvider.from_config(
        git_provider_app_by_id(session, organization_id, app_id), aws_config
    )

    group_app_installation = git_provider_app_installation_by_id(
        session, installation_id
    )
    if (
        not group_app_installation
        or group_app_installation.organization_id != organization_id
    ):
        logger.error(
            f"Group app installation not found for user {user_id} and app {app_id}"
        )
        raise ValueError("Group app installation not found for organization")
    repositories = []
    repositories.extend(git_provider.fetch_group_repos(group_app_installation))

    return repositories


def clone_git_repository(
    session: Session,
    organization_id: str,
    user_id: str,
    app_id: str,
    git_repo: GitRepository,
    upload_key: str,
    bucket_name: str,
    aws_config: AWSClientConfig,
) -> str:
    existing_app_install = git_provider_app_installation_by_org_id(
        session, organization_id, app_id
    )
    if not existing_app_install:
        logger.error(f"App installation not found for user {user_id} and app {app_id}")
        raise ValueError("App installation not found for user")

    git_provider = GitLabProvider.from_config(
        git_provider_app_by_id(session, organization_id, app_id), aws_config
    )
    try:
        return git_provider.clone_repository(
            git_repo, user_id, organization_id, upload_key, bucket_name
        )
    except GitProviderAppRevokeError as e:
        logger.error(
            f"Access token expired or was revoked for user {user_id} and app {app_id}"
        )
        # if we get an error fetching repositories, getting the access token failed and need to uninstall the app and force the user to re-authenticate/reinstall
        handle_user_app_revoke(
            session, organization_id, app_id, str(existing_app_install.id), aws_config
        )
        raise e


def handle_user_app_revoke(
    session: Session,
    organization_id: str,
    app_id: str,
    installation_id: str,
    aws_config: AWSClientConfig,
) -> None:
    logger.info(f"Uninstalling app for installation ID {installation_id}")
    delete_git_provider_app_install(session, organization_id, app_id, installation_id)
    AWSSecretManagementStrategy(config=aws_config).delete_secret(
        format_secret_name(APP_INSTALL_SECRET_NAME_PREFIX, str(installation_id))
    )


def handle_group_access_revoke(
    session: Session,
    organization_id: str,
    app_id: str,
    installation_id: str,
    aws_config: AWSClientConfig,
) -> None:
    logger.info(f"Uninstalling app for installation ID {installation_id}")
    delete_git_provider_app_install(session, organization_id, app_id, installation_id)
    AWSSecretManagementStrategy(config=aws_config).delete_secret(
        format_secret_name(APP_INSTALL_GAT_NAME_PREFIX, str(installation_id))
    )


def handle_delete_git_provider_app(
    session: Session, organization_id: str, app_id: str, aws_config: AWSClientConfig
) -> None:
    # delete all app installations
    app_installations = git_provider_app_installation_by_org_id(
        session, organization_id, app_id
    )
    for app_install in app_installations:
        handle_group_access_revoke(
            session, organization_id, app_id, str(app_install.id), aws_config
        )

    git_provider_app = git_provider_app_by_id(session, organization_id, app_id)
    session.delete(git_provider_app)
    session.commit()
    return None


def validate_group_access_token(
    session: Session,
    organization_id: str,
    app_id: str,
    access_token: str,
    aws_config: AWSClientConfig,
) -> bool:
    git_provider = GitLabProvider.from_config(
        git_provider_app_by_id(session, organization_id, app_id), aws_config
    )
    try:
        token_user = git_provider.auth_strategy.token_user(access_token)
        return token_user is not None
    except Exception:
        logger.exception(
            f"Error validating group access token for app {app_id} and org {organization_id}"
        )
        return False
