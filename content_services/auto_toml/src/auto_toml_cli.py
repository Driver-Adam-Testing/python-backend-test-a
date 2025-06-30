import argparse
import asyncio
import os
from uuid import UUID

from auto_toml import AutoToml


async def generate_command(args: argparse.Namespace) -> None:
    if args.env in ["dev", "prod"]:
        os.environ["MODAL_ENVIRONMENT"] = args.env
        from modal import Cls

        AutoTomlModal = Cls.from_name("auto_toml", "AutoTomlModal")
        auto_toml_modal = AutoTomlModal()

        if args.node_ids:
            node_ids = [node_id.strip() for node_id in args.node_ids.split(",")]
            result = auto_toml_modal.generate_from_node_ids.remote(
                node_ids=node_ids,
                enable_auto_scaling=args.auto_scale,
                document_goal=args.goal,
            )
        else:
            result = auto_toml_modal.generate_from_page_id.remote(
                page_id=args.page_id,
                enable_auto_scaling=args.auto_scale,
                document_goal=args.goal,
            )

    else:
        if args.node_ids:
            node_ids = [node_id.strip() for node_id in args.node_ids.split(",")]
            auto_toml = AutoToml.from_node_ids(
                node_ids=node_ids, enable_auto_scaling=args.auto_scale
            )
        else:
            auto_toml = AutoToml.from_page_id(
                page_id=UUID(args.page_id), enable_auto_scaling=args.auto_scale
            )

        result = await auto_toml.generate(document_goal=args.goal)

    with open(args.output, "w") as f:
        f.write(result)


async def append_command(args: argparse.Namespace) -> None:
    with open(args.toml_file) as f:
        user_toml = f.read()

    if args.env in ["dev", "prod"]:
        os.environ["MODAL_ENVIRONMENT"] = args.env
        from modal import Cls

        AutoTomlModal = Cls.from_name("auto_toml", "AutoTomlModal")
        auto_toml_modal = AutoTomlModal()

        if args.node_ids:
            node_ids = [node_id.strip() for node_id in args.node_ids.split(",")]
            result = auto_toml_modal.append_from_node_ids.remote(
                node_ids=node_ids,
                enable_auto_scaling=args.auto_scale,
                user_toml=user_toml,
            )
        else:
            result = auto_toml_modal.append_from_page_id.remote(
                page_id=args.page_id,
                enable_auto_scaling=args.auto_scale,
                user_toml=user_toml,
            )
    else:
        # Use local execution
        if args.node_ids:
            node_ids = [node_id.strip() for node_id in args.node_ids.split(",")]
            auto_toml = AutoToml.from_node_ids(
                node_ids=node_ids, enable_auto_scaling=args.auto_scale
            )
        else:
            auto_toml = AutoToml.from_page_id(
                page_id=UUID(args.page_id), enable_auto_scaling=args.auto_scale
            )

        result = await auto_toml.append(user_toml=user_toml)

    with open(args.output, "w") as f:
        f.write(result)


def main() -> None:
    parser = argparse.ArgumentParser(description="Auto TOML CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    generate_parser = subparsers.add_parser(
        "generate", help="Generate TOML from document goal"
    )
    generate_parser.add_argument(
        "--goal", required=True, help="Document goal description"
    )
    generate_parser.add_argument(
        "--output",
        default="output.toml",
        help="Output file path (default: output.toml)",
    )
    generate_parser.add_argument(
        "--auto-scale",
        action="store_true",
        help="Enable auto-scaling source contents to improve latency",
    )
    generate_parser.add_argument(
        "--env",
        choices=["local", "dev", "prod"],
        default="local",
        help="Execution environment: local (default), dev, or prod",
    )

    generate_source_group = generate_parser.add_mutually_exclusive_group(required=True)
    generate_source_group.add_argument(
        "--node-ids", help="Comma-separated list of node IDs"
    )
    generate_source_group.add_argument("--page-id", help="Page ID (UUID)")

    append_parser = subparsers.add_parser("append", help="Append to existing TOML file")
    append_parser.add_argument(
        "--toml-file", required=True, help="Path to existing TOML file"
    )
    append_parser.add_argument(
        "--output",
        default="output.toml",
        help="Output file path (default: output.toml)",
    )
    append_parser.add_argument(
        "--auto-scale",
        action="store_true",
        help="Enable auto-scaling source contents to improve latency",
    )
    append_parser.add_argument(
        "--env",
        choices=["local", "dev", "prod"],
        default="local",
        help="Execution environment: local (default), dev, or prod",
    )

    append_source_group = append_parser.add_mutually_exclusive_group(required=True)
    append_source_group.add_argument(
        "--node-ids", help="Comma-separated list of node IDs"
    )
    append_source_group.add_argument("--page-id", help="Page ID (UUID)")

    args = parser.parse_args()

    if args.command == "generate":
        asyncio.run(generate_command(args))
    elif args.command == "append":
        asyncio.run(append_command(args))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
