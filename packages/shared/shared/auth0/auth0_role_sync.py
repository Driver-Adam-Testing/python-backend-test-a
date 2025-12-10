"""Auth0 Role Synchronization Module.

This module synchronizes Auth0 organization roles with the database organization memberships.
It ensures that the roles stored in the database match the authoritative roles in Auth0.

Key Features:
    - Fetches all organization memberships from the database
    - Queries Auth0 for each user's roles in their respective organizations
    - Updates database roles to match Auth0 (Admin -> super_admin, Editor -> member)
    - Removes memberships for users with no roles in Auth0
    - Supports dry-run mode for safe preview of changes
    - Provides detailed verbose logging option

Role Mapping:
    Auth0 "Admin" -> OrgRole.super_admin
    Auth0 "Editor" -> OrgRole.member
    No roles or unrecognized -> OrgRole.member (default)

Usage:
    from shared.auth0.auth0_role_sync import run_role_sync

    # Preview changes without modifying database
    stats = await run_role_sync(dry_run=True, verbose=True)

    # Apply changes to database
    stats = await run_role_sync(dry_run=False, verbose=False)
"""

import os
from collections import defaultdict

from database.db import async_engine
from database.models import OrgMembership
from database.models_enums import OrgRole
from sqlmodel.ext.asyncio.session import AsyncSession

from shared.auth0.auth0_async import AsyncAuth0Service


async def fetch_org_memberships_from_db(
    db_session: AsyncSession,
) -> list[OrgMembership]:
    # fetch all organizations

    from database.models import OrgMembership
    from sqlalchemy import select

    result = db_session.exec(select(OrgMembership))
    return (await result).scalars().all()


AUTH0_TO_ORG_ROLE = {"Admin": OrgRole.org_super_admin, "Editor": OrgRole.org_member}


def _determine_role(auth0_roles: list[dict]) -> OrgRole:
    """Determine DB role from Auth0 roles, prioritizing Admin > Editor > Member."""
    mapped_roles = [
        role for role in auth0_roles if role.get("name") in AUTH0_TO_ORG_ROLE
    ]

    if not mapped_roles:
        return OrgRole.org_member  # Default

    # Priority: Admin > Editor
    admin_role = next(
        (AUTH0_TO_ORG_ROLE[r["name"]] for r in mapped_roles if r["name"] == "Admin"),
        None,
    )
    editor_role = next(
        (AUTH0_TO_ORG_ROLE[r["name"]] for r in mapped_roles if r["name"] == "Editor"),
        None,
    )
    return admin_role or editor_role or OrgRole.org_member


def print_summary(stats: dict, dry_run: bool) -> None:
    """Print role sync summary statistics."""
    print("\n" + "=" * 60)
    print("ROLE SYNC SUMMARY")
    print("=" * 60)

    if dry_run:
        print("DRY RUN - No changes were saved")
        print("-" * 60)

    print(f"Memberships checked: {stats['memberships_checked']}")
    print(f"Roles updated: {stats['roles_updated']}")
    print(f"Roles skipped (unchanged): {stats['roles_skipped']}")
    print(f"Memberships deleted: {stats['memberships_deleted']}")

    if stats["errors"]:
        print(f"\nErrors ({len(stats['errors'])}):")
        for error in stats["errors"][:10]:
            print(f"  - {error}")
        if len(stats["errors"]) > 10:
            print(f"  ... and {len(stats['errors']) - 10} more")

    print("=" * 60 + "\n")


async def _sync_organization(
    db_session: AsyncSession,
    auth0_client: AsyncAuth0Service,
    org_id: str,
    memberships: list[OrgMembership],
    verbose: bool,
) -> dict:
    """Sync roles for a single organization."""
    org_stats = {
        "checked": 0,
        "updated": 0,
        "skipped": 0,
        "deleted": 0,
        "errors": [],
    }

    for membership in memberships:
        try:
            user_id = membership.user_id

            if verbose:
                print(f"  Checking user {user_id}...")

            auth0_roles = await auth0_client.list_user_organization_roles_async(
                org_id, user_id
            )

            # If user has no roles in Auth0, remove the membership
            if len(auth0_roles) == 0:
                print(f"  [DELETE] {user_id} - no roles in Auth0")
                await db_session.delete(membership)
                org_stats["deleted"] += 1
            else:
                # Determine the role based on Auth0 roles
                new_role = _determine_role(auth0_roles)

                # Update membership if role has changed
                if membership.role != new_role:
                    print(f"  [UPDATE] {user_id}: {membership.role} -> {new_role}")
                    membership.role = new_role
                    db_session.add(membership)
                    org_stats["updated"] += 1
                else:
                    if verbose:
                        print(f"  [SKIP] {user_id}: {membership.role} (unchanged)")
                    org_stats["skipped"] += 1

            org_stats["checked"] += 1

        except Exception as e:
            error_msg = f"{user_id}: {e}"
            org_stats["errors"].append(error_msg)
            print(f"  [ERROR] {error_msg}")

    return org_stats


async def run_role_sync(dry_run: bool = False, verbose: bool = False) -> dict:
    """Sync Auth0 roles to database organization memberships.

    Args:
        dry_run: If True, performs sync but rolls back changes (no database modifications)
        verbose: If True, prints detailed progress information

    Returns:
        Dictionary with sync statistics
    """
    stats = {
        "memberships_checked": 0,
        "roles_updated": 0,
        "roles_skipped": 0,
        "memberships_deleted": 0,
        "errors": [],
    }

    if dry_run:
        print("\n" + "=" * 60)
        print("DRY RUN MODE - No changes will be saved to database")
        print("=" * 60 + "\n")

    auth0_client = AsyncAuth0Service(
        auth0_mgmt_domain=os.environ["AUTH0_MGMT_API_DOMAIN"],
        auth0_mgmt_client_id=os.environ["AUTH0_MGMT_API_CLIENT_ID"],
        auth0_mgmt_client_secret=os.environ["AUTH0_MGMT_API_CLIENT_SECRET"],
        auth0_domain=os.environ["AUTH0_DOMAIN"],
        auth0_client_id=os.environ["AUTH0_CLIENT_ID"],
    )

    async with AsyncSession(async_engine) as db_session:
        # Fetch and group memberships by organization
        print("Fetching all organization memberships from database...")
        all_memberships = await fetch_org_memberships_from_db(db_session)

        memberships_by_org = defaultdict(list)
        for membership in all_memberships:
            memberships_by_org[membership.org_id].append(membership)

        total_orgs = len(memberships_by_org)
        print(
            f"Found {len(all_memberships)} memberships across {total_orgs} organizations\n"
        )

        # Process each organization
        for idx, (org_id, org_memberships) in enumerate(
            memberships_by_org.items(), start=1
        ):
            print(f"[{idx}/{total_orgs}] Processing organization: {org_id}")
            print(f"  Members: {len(org_memberships)}")

            org_stats = await _sync_organization(
                db_session, auth0_client, org_id, org_memberships, verbose
            )

            # Update global stats
            stats["memberships_checked"] += org_stats["checked"]
            stats["roles_updated"] += org_stats["updated"]
            stats["roles_skipped"] += org_stats["skipped"]
            stats["memberships_deleted"] += org_stats["deleted"]
            stats["errors"].extend(
                [f"Org {org_id}: {err}" for err in org_stats["errors"]]
            )

            # Print org summary
            changes = org_stats["updated"] + org_stats["deleted"]
            if changes > 0 or org_stats["errors"]:
                print(
                    f"  Summary: {org_stats['updated']} updated, {org_stats['skipped']} skipped, "
                    f"{org_stats['deleted']} deleted, "
                    f"{org_stats['errors'] and len(org_stats['errors']) or 0} errors"
                )
            elif verbose:
                print(f"  Summary: {org_stats['skipped']} skipped, no changes needed")

            print()  # Blank line between orgs

        # Atomic commit/rollback
        if dry_run:
            print("=" * 60)
            print("Dry run complete - rolling back all changes")
            print("=" * 60)
            await db_session.rollback()
        else:
            print("=" * 60)
            print("Committing changes to database...")
            print("=" * 60)
            await db_session.commit()

    print_summary(stats, dry_run)
    return stats
