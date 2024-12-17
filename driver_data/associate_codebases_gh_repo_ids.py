import argparse
import logging

from app.repositories.github_app_installations_repository import (
    GithubAppInstallationsRepository,
)
from app.utils.gh_ops import fetch_repos
from database.db import engine
from database.models_v1 import DerivedContent, DerivedContentType, Workspace
from sqlmodel import Session, select


def associate_codebase_with_gh_repo_ids(
    session: Session,
    dry_run: bool,
):
    """Associates codebases with matching GitHub Installation IDs."""

    gh_app_installation_repo = GithubAppInstallationsRepository(session)
    try:
        all_installation_ids = gh_app_installation_repo.get_all(limit=1000)
        org_repos = {}
        org_codebases = {}
        for installation_id_record in all_installation_ids:
            installation_id = installation_id_record.github_app_installation_id
            organization_id = installation_id_record.organization_id
            print(
                f"\nLooking for repos tied to installation {installation_id} in {organization_id}"
            )
            if organization_id not in org_repos:
                org_repos[organization_id] = fetch_repos(session, organization_id)
            if organization_id not in org_codebases:
                org_codebases[organization_id] = session.exec(
                    select(DerivedContent)
                    .join(DerivedContentType)
                    .join(Workspace)
                    .where(
                        DerivedContentType.type_name == "codebase",
                        Workspace.organization_id == organization_id,
                    )
                ).all()

            for repo in org_repos[organization_id]:
                print(f"Searching for repo name = {repo["name"]}...")
                for codebase in org_codebases[organization_id]:
                    if repo["name"] == codebase.relative_path:
                        print(
                            f"Adding repo name: {repo["name"]}, repo id: {repo["id"]}, to metadata for codebase id: {codebase.id}"
                        )
                        if not dry_run:
                            codebase.misc_metadata = {
                                "github_repo_id": str(repo["id"]),
                            }
                            session.add(codebase)
                            session.commit()

            print(
                "Migration completed successfully."
                if not dry_run
                else "Dry run completed successfully."
            )
    except Exception:
        logging.exception("Migration failed")


def main():
    parser = argparse.ArgumentParser(
        description="Associate existing codebases with GitHub app IDs."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate the migration without making any database changes.",
    )
    args = parser.parse_args()

    with Session(engine) as session:
        associate_codebase_with_gh_repo_ids(session, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
