from database.models_v1 import GitProviderApp, GitProviderAppInstallation
from sqlmodel import Session, select


### DATABASE OPERATIONS ###
def git_provider_apps_by_org_id(
    session: Session, organization_id: str
) -> list[GitProviderApp]:
    query = select(GitProviderApp).where(
        GitProviderApp.owner_organization_id == organization_id,
        GitProviderApp.shared_provider == False,  # noqa: E712
    )

    return session.exec(query).all()


def git_provider_app_by_id(
    session: Session, organization_id: str, app_id: str
) -> GitProviderApp:
    query = select(GitProviderApp).where(
        GitProviderApp.id == app_id,
        GitProviderApp.owner_organization_id == organization_id,
    )

    return session.exec(query).first()


def git_provider_app_installation_by_user_id(
    session: Session, organization_id: str, app_id: str, user_id: str
) -> GitProviderAppInstallation | None:
    query = select(GitProviderAppInstallation).where(
        GitProviderAppInstallation.git_provider_app_id == app_id,
        GitProviderAppInstallation.user_id == user_id,
        GitProviderAppInstallation.organization_id == organization_id,
    )
    return session.exec(query).first()


def delete_git_provider_app_install(
    session: Session, organization_id: str, app_id: str, installation_id: str
) -> None:
    query = select(GitProviderAppInstallation).where(
        GitProviderAppInstallation.id == installation_id,
        GitProviderAppInstallation.git_provider_app_id == app_id,
        GitProviderAppInstallation.organization_id == organization_id,
    )
    app = session.exec(query).first()
    session.delete(app)
    session.commit()
    return None
