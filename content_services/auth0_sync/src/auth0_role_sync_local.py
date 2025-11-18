import argparse
import asyncio

from dotenv import load_dotenv
from shared.auth0.auth0_role_sync import run_role_sync

load_dotenv()


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Sync Auth0 organization roles to database"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run sync without committing changes to database",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Print detailed progress information",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(run_role_sync(dry_run=args.dry_run, verbose=args.verbose))
