import concurrent.futures
import os
from functools import cache
from pathlib import Path

from database.models_v2 import Node, PrimaryAsset, Version
from database.models_v2_enums import PrimaryAssetKind
from shared.usage.utils import bytes_to_sloc
from sqlalchemy import create_engine
from sqlalchemy.orm.attributes import flag_modified
from sqlmodel import Session, select

# database_url = str(settings.SQLALCHEMY_DATABASE_URI)
database_url = os.getenv("SOURCE_DATABASE_URL")
engine = create_engine(database_url)


@cache
def load_extension_and_name_mapping() -> dict:
    from collections import defaultdict

    import yaml

    with open("languages.yml") as f:
        language_dict = yaml.safe_load(f)
    extension_map = defaultdict(list)
    name_map = defaultdict(list)
    for lang in language_dict:
        if language_dict[lang].get("extensions"):
            for ext in language_dict[lang]["extensions"]:
                extension_map[ext].append(lang)
        if language_dict[lang].get("filenames"):
            for name in language_dict[lang]["filenames"]:
                name_map[name].append(lang)
    return extension_map, name_map


def get_file_type_from_extension(extension: str) -> str | None:
    extension_map = load_extension_and_name_mapping()[0]
    file_type = extension_map.get(extension)

    if extension == ".h":
        return "Header"
    elif file_type and len(file_type) == 1:
        return file_type[0]
    return None


def get_file_type_from_filename(filename: str) -> str | None:
    name_map = load_extension_and_name_mapping()[1]
    file_type = name_map.get(filename)

    if file_type and len(file_type) == 1:
        return file_type[0]
    return None


def update_stats_for_version_id(version_id: str) -> None:
    with Session(engine) as session:
        nodes_stmt = select(Node).where(Node.version_id == version_id)
        nodes = session.exec(nodes_stmt).all()
        print(f"Found {len(nodes)} nodes for version {version_id}")
        for node in nodes:
            if node.kind == "CODEBASE_DIRECTORY":
                stats = node.misc_metadata
                if stats is not None and stats.get("analyzable_bytes") is not None:
                    print(f"Skipping version {version_id} because it is already set")
                    return
        for node in nodes:
            if node.kind == "CODEBASE_FILE" and node.misc_metadata is not None:
                # Adds the language stat to the file
                file_stats = node.misc_metadata
                if file_stats.get("language") is None:
                    if file_stats["is_analyzable"]:
                        file_type = get_file_type_from_extension(
                            file_stats["extension"]
                        )
                        if not file_type:
                            file_type = get_file_type_from_filename(
                                Path(node.relative_path).name
                            )
                        if not file_type:
                            file_type = "Other"
                        file_stats["language"] = file_type
                    else:
                        file_stats["language"] = "N/A"
                    node.misc_metadata = file_stats
                    flag_modified(node, "misc_metadata")
                    session.add(node)
        # session.commit()
        for node in nodes:
            if node.kind == "CODEBASE_DIRECTORY":
                directory_stats = {
                    "analyzable_bytes": 0,
                    "analyzable_files": 0,
                    "analyzable_sloc": 0,
                    "total_bytes": 0,
                    "total_files": 0,
                    "total_sloc": 0,
                    "analyzable_files_by_type": {},
                    "analyzable_bytes_by_type": {},
                    "analyzable_sloc_by_type": {},
                    "analyzable_files_by_extension": {},
                    "analyzable_bytes_by_extension": {},
                    "analyzable_sloc_by_extension": {},
                }
                relative_path = node.relative_path

                for child_node in nodes:
                    if (
                        child_node.kind == "CODEBASE_FILE"
                        and child_node.relative_path.startswith(relative_path)
                        and child_node.misc_metadata is not None
                    ):
                        file_path = Path(child_node.relative_path)
                        directory_stats["total_bytes"] += child_node.misc_metadata[
                            "size"
                        ]
                        directory_stats["total_files"] += 1
                        if (
                            child_node.misc_metadata["is_analyzable"]
                            and not child_node.misc_metadata["is_blacklisted"]
                            and not child_node.misc_metadata.get("is_ignored", False)
                        ):
                            file_stats = child_node.misc_metadata
                            file_type = file_stats.get("language")

                            if file_type is None:
                                file_type = "Other"
                                print("No file type")
                            if (
                                file_type
                                not in directory_stats["analyzable_files_by_type"]
                            ):
                                directory_stats["analyzable_files_by_type"][
                                    file_type
                                ] = 0
                                directory_stats["analyzable_bytes_by_type"][
                                    file_type
                                ] = 0
                            directory_stats["analyzable_files_by_type"][file_type] += 1
                            directory_stats["analyzable_bytes_by_type"][file_type] += (
                                file_stats["size"]
                            )

                            file_extension = file_path.suffix
                            if (
                                file_extension
                                not in directory_stats["analyzable_files_by_extension"]
                            ):
                                directory_stats["analyzable_files_by_extension"][
                                    file_extension
                                ] = 0
                                directory_stats["analyzable_bytes_by_extension"][
                                    file_extension
                                ] = 0
                            directory_stats["analyzable_files_by_extension"][
                                file_extension
                            ] += 1
                            directory_stats["analyzable_bytes_by_extension"][
                                file_extension
                            ] += file_stats["size"]
                            directory_stats["analyzable_bytes"] += file_stats["size"]
                            directory_stats["analyzable_files"] += 1
                directory_stats["analyzable_sloc"] = bytes_to_sloc(
                    directory_stats["analyzable_bytes"]
                )
                directory_stats["total_sloc"] = bytes_to_sloc(
                    directory_stats["total_bytes"]
                )
                for type, bytes in directory_stats["analyzable_bytes_by_type"].items():
                    directory_stats["analyzable_sloc_by_type"][type] = bytes_to_sloc(
                        bytes
                    )
                for ext, bytes in directory_stats[
                    "analyzable_bytes_by_extension"
                ].items():
                    directory_stats["analyzable_sloc_by_extension"][ext] = (
                        bytes_to_sloc(bytes)
                    )
                node.misc_metadata = directory_stats
                flag_modified(node, "misc_metadata")
                session.add(node)
        session.commit()


with Session(engine) as session:
    versions_stmt = (
        select(Version)
        .join(PrimaryAsset)
        .where(PrimaryAsset.kind == PrimaryAssetKind.CODEBASE)
        # .options(selectinload(Version.primary_asset))
    )

    versions = session.exec(versions_stmt).all()

with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    futures = []
    for version in versions:
        futures.append(executor.submit(update_stats_for_version_id, version.id))
    for future in concurrent.futures.as_completed(futures):
        try:
            res = future.result()
            print(f"Finished updating stats for version {res}")
        except:
            print(f"Error updating stats for version {version.id}")
            raise
# for version in versions:
#     print(f"Updating stats for version {version.id}")
#     try:
#         update_stats_for_version_id(version.id)
#     except Exception as e:
#         print(f"Error updating stats for version {version.id}: {e}")
#         raise e
