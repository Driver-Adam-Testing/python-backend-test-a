import argparse
import json
import logging

import requests
from app.core.config import settings
from app.repositories.github_app_installations_repository import (
    GithubAppInstallationsRepository,
)
from app.services.auth0_service import Auth0Service
from app.utils.aws_secrets_manager import format_secret_key, read_secret, write_secret
from auth0.management import Auth0
from database.db import engine
from sqlmodel import Session

logging.basicConfig(level=logging.INFO)


def get_installation_ids_from_github_token(access_token: str) -> list[str] | None:
    """
    Retrieves the GitHub App installation ID for the given GitHub user token.
    """
    headers = {
        "Authorization": f"token {access_token}",
        "Accept": "application/vnd.github+json",
    }
    url = "https://api.github.com/user/installations"
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        logging.error(
            f"GitHub API request failed: {response.status_code} - {response.text}"
        )
        return None

    installations = response.json().get("installations", [])
    if not installations:
        logging.warning(
            "No installations found for the user. Maybe they uninstalled the app?"
        )
        return None

    return [installation["id"] for installation in installations]


def get_all_users(auth0_client: Auth0, per_page: int = 100) -> list[dict]:
    users = []
    page = 0

    while True:
        response = auth0_client.users.list(per_page=per_page, page=page)
        batch = response["users"]

        if not batch:
            break

        users.extend(batch)
        page += 1

    logging.info(f"Fetched {len(users)} users from Auth0.")
    return users


def get_all_organizations(
    auth0_client: Auth0, user_id: str, per_page: int = 100
) -> list[dict]:
    """Fetch all organizations for a given user from Auth0 by handling pagination."""
    organizations = []
    page = 0

    while True:
        response = auth0_client.users.list_organizations(
            user_id, per_page=per_page, page=page
        )
        batch = response["organizations"]

        if not batch:
            break

        organizations.extend(batch)
        page += 1

    logging.info(f"Fetched {len(organizations)} organizations for user {user_id}.")
    return organizations


def is_token_valid(token):
    if token is None:
        return False
    url = "https://api.github.com/user"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    return response.status_code == 200


def refresh_access_token(refresh_token):
    url = "https://github.com/login/oauth/access_token"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": settings.GH_CLIENT_ID,
        "client_secret": settings.GH_CLIENT_SECRET,
    }
    headers = {"Accept": "application/json"}
    response = requests.post(url, data=data, headers=headers)
    return (
        response.json()
    )  # This should contain the new 'access_token' and optionally a new 'refresh_token'


def migrate_user_installation_ids(
    auth0_service: Auth0Service,
    gh_app_installation_repo: GithubAppInstallationsRepository,
    dry_run: bool,
):
    """Migrates users with GitHub tokens from secrets to the database."""
    try:
        mgmt_api_token = auth0_service.get_mgmt_api_token()
        auth0_client = Auth0(auth0_service.auth0_mgmt_domain, mgmt_api_token)

        users = get_all_users(auth0_client)

        for user in users:
            user_id = user["user_id"]
            user_email = user["email"]
            logging.info(f"\n\nProcessing user: {user_email} ({user_id})")
            orgs = get_all_organizations(auth0_client, user_id)

            for org in orgs:
                org_id = org["id"]

                secret_key = format_secret_key(org_id, user_id, "github")
                # logging.info(f"Processing {secret_key}")
                secret = read_secret(secret_key)
                if not secret:
                    logging.debug(
                        f"Failed reading github token secret for {user_email} ({user_id}) in org {org['name']} ({org_id}). Skipping."
                    )
                    logging.info("No existing secret found, continuing...")
                    continue

                secret_string = secret["SecretString"]
                secret_sauce = json.loads(secret_string)
                github_token = secret_sauce.get("access_token", None)
                if not is_token_valid(github_token):
                    logging.info("Token is invalid, refreshing...")
                    try:
                        new_tokens = refresh_access_token(secret_sauce["refresh_token"])
                        secret_value = json.dumps(new_tokens)
                        if new_tokens and "access_token" in new_tokens:
                            write_secret(secret_key, secret_value)
                            logging.info("Saved new tokens.")
                            github_token = new_tokens["access_token"]
                        else:
                            logging.info(
                                "Did not receive access tokens when refreshing, skipping..."
                            )
                            continue
                    except Exception:
                        logging.info(
                            f"Unable to refresh tokens for {secret_key}, skipping..."
                        )
                        continue

                installation_ids = get_installation_ids_from_github_token(github_token)
                if not installation_ids or len(installation_ids) == 0:
                    logging.warning(
                        f"Failed to retrieve installation IDs for user {user_email} ({user_id}) in {org['name']} ({org_id}). Skipping."
                    )
                    continue

                for installation_id in installation_ids:
                    if not gh_app_installation_repo.exists(org_id, installation_id):
                        if dry_run:
                            logging.info(
                                f"Dry Run: Would create record - "
                                f"org_id={org_id}, installation_id={installation_id}"
                            )
                        if not dry_run:
                            gh_app_installation_repo.create(
                                organization_id=org_id,
                                github_app_installation_id=installation_id,
                            )
                            logging.info(
                                f"Successfully created organization installation for org id = {org_id} and installation id = {installation_id} in database."
                            )

        logging.info(
            "Migration completed successfully."
            if not dry_run
            else "Dry run completed successfully."
        )
    except Exception:
        logging.exception("Migration failed")


def main():
    parser = argparse.ArgumentParser(
        description="Migrate users from secrets to the database."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate the migration without making any database changes.",
    )
    args = parser.parse_args()

    auth0_service = Auth0Service()
    with Session(engine) as session:
        gh_app_installation_repo = GithubAppInstallationsRepository(session)
        migrate_user_installation_ids(
            auth0_service, gh_app_installation_repo, dry_run=args.dry_run
        )


if __name__ == "__main__":
    main()
