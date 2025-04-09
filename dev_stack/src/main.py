import argparse
import json
from pathlib import Path

from developer_setup import setup_developer_resources, teardown_developer_resources
from models import Developer


def load_developer_state(full_name: str) -> Developer | None:
    filename = f"{full_name.lower().replace(' ', '_')}_state.json"
    file_path = Path("state") / filename

    if not file_path.exists():
        print(f"❌ No state file found for developer: {full_name}")
        return None

    try:
        with open(file_path) as f:
            state = json.load(f)
            return Developer.model_validate(state)
    except Exception as e:
        print(f"❌ Error loading state file: {e!s}")
        return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Cloud Local CLI")

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Setup command
    setup_parser = subparsers.add_parser("setup", help="Setup developer environment")
    setup_parser.add_argument("--name", type=str, help="Developer name", required=True)
    setup_parser.add_argument(
        "--email", type=str, help="Developer email", required=True
    )
    setup_parser.add_argument(
        "--region", type=str, default="us", help="Ngrok region (default: us)"
    )

    # Teardown command
    teardown_parser = subparsers.add_parser(
        "teardown", help="Teardown developer environment"
    )
    teardown_parser.add_argument(
        "--name", type=str, help="Developer name", required=True
    )

    args = parser.parse_args()

    if args.command == "setup":
        setup_developer_resources(
            full_name=args.name, email=args.email, region=args.region
        )
    elif args.command == "teardown":
        developer = load_developer_state(args.name)
        if developer:
            teardown_developer_resources(developer)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
