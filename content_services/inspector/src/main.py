import hashlib
import os
import uuid
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from enum import Enum
from pathlib import Path
from uuid import UUID

import modal
from onboarding.onboard import (
    connect_unconnected_repos,
)

inspection_image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("git")
    .add_local_dir(local_path="../../driver_db", remote_path="/driver_db", copy=True)
    .add_local_dir(
        local_path="../../packages/shared", remote_path="/shared_pkg", copy=True
    )
    .pip_install(
        [
            "boto3",
            "requests",
            "openai==1.99.1",
            "pydantic>=2.8.2",
            "tiktoken",
            "/shared_pkg",
            "tree-sitter==0.24.0",
            "tree-sitter-c==0.23.4",
            "tree-sitter-cpp==0.23.2",
            "tree-sitter-java==0.23.5",
            "tree-sitter-python==0.23.6",
            "tree-sitter-c-sharp==0.23.1",
            "tree-sitter-typescript==0.23.2",
            "chardet",
        ]
    )
    .add_local_python_source(
        "inspection",
        "modal_funcs",
        "onboarding",
        "shared",
        "tasks",
        "utils",
        "common",
        "database",
        copy=True,
        ignore=lambda p: False,  # recent modal version only copy .py by default, but we have text files, for example, that we want
    )
)

from common import app  # noqa: E402
from utils.dag import FileTreeDag, Node, NodeKind, NodeStatus  # noqa: E402

with inspection_image.imports():
    from tasks import (
        CodebaseTaggingTask,
        CSymbolTableTask,
        EmbeddingTask,
        FileTechDocTask,
        FolderTechDocTask,
        SymbolsTask,
        TopLevelDocsTask,
    )
    from utils.task import TaskManager


# TODO considering using concurrent inputs when we're just calling open AI. This should
# save some cost (though costs are negligible today)

TECH_DOC_THREAD_POOL = ThreadPoolExecutor(max_workers=2)


class InspectionMode(Enum):
    NORMAL = "normal"
    RESUME = "resume"
    RERUN = "rerun"

    @classmethod
    def from_str(cls, mode_str: str) -> "InspectionMode":
        try:
            return cls(mode_str.lower())
        except ValueError:
            valid_modes = ", ".join([mode.value for mode in cls])
            raise ValueError(
                f"Invalid mode '{mode_str}'. Must be one of: {valid_modes}."
            )


async def get_result_loading_config(
    inspection_mode: InspectionMode,
    version_id: uuid.UUID,
    previous_version_id: uuid.UUID | None = None,
) -> list[tuple[uuid.UUID, set[NodeStatus]]]:
    from utils.db import try_get_latest_run_from_version_id

    result_loading_config = []
    is_diff = previous_version_id is not None

    match inspection_mode:
        case InspectionMode.NORMAL:
            existing_run_id_for_prev_version = (
                await try_get_latest_run_from_version_id(previous_version_id)
                if is_diff
                else None
            )
            existing_run_id_for_current_version = None
        case InspectionMode.RESUME:
            existing_run_id_for_prev_version = (
                await try_get_latest_run_from_version_id(previous_version_id)
                if is_diff
                else None
            )
            existing_run_id_for_current_version = (
                await try_get_latest_run_from_version_id(version_id)
            )
        case InspectionMode.RERUN:
            existing_run_id_for_prev_version = (
                await try_get_latest_run_from_version_id(previous_version_id)
                if is_diff
                else None
            )
            existing_run_id_for_current_version = None
        case _:
            raise ValueError("Invalid inspection mode")

    if existing_run_id_for_prev_version:
        result_loading_config.append(
            (existing_run_id_for_prev_version, {NodeStatus.UNMODIFIED})
        )
    if existing_run_id_for_current_version:
        result_loading_config.append(
            (existing_run_id_for_current_version, set(NodeStatus))
        )

    return result_loading_config


@app.function(
    image=inspection_image,
    secrets=[
        modal.Secret.from_name("db"),
        modal.Secret.from_name("aws-inspector-s3"),
        modal.Secret.from_name("open-ai"),
    ],
    proxy=modal.Proxy.from_name("my-proxy")
    if os.environ["MODAL_ENVIRONMENT"] in ["dev", "staging", "prod"]
    else None,
    memory=4096,
    timeout=3600 * 12,
    region="us-east",
    max_containers=5,
    cpu=1.0,
)
async def inspect_db(
    version_id: uuid.UUID,
    inspection_mode: InspectionMode = InspectionMode.NORMAL,
) -> None:
    import tempfile

    import boto3
    from database.models_enums import NodeKind as DbNodeKind
    from database.models_enums import VersionStatus
    from modal_funcs import export_tech_docs_to_zip
    from onboarding.onboard_utils import (
        process_and_upload_all_files_in_parallel,
        set_codebase_status,
        unpack_archive_to_finalized_path,
    )
    from utils.db import (
        create_inspector_run,
        delete_version_by_id,
        get_analyzable_nodes_by_version_id,
        get_version_by_id,
        try_get_prev_version,
    )
    from utils.git_diff import (
        CodeDiffParams,
        InsufficientBalanceError,
        compute_and_log_code_diff_size_in_bytes,
    )
    from utils.io import download_all_source_files_in_parallel

    try:
        # Get the Version and check if it has previous_version_id
        version = await get_version_by_id(version_id)
        org_id = version.primary_asset.organization_id
        org_hashed_id = hashlib.sha256(org_id.encode()).hexdigest()[:63]

        previous_version = await try_get_prev_version(version_id)
        previous_version_id = previous_version.id if previous_version else None

        codebase_name = version.primary_asset.display_name

        result_loading_config = await get_result_loading_config(
            inspection_mode, version_id, previous_version_id
        )
        print("Result loading config: ", result_loading_config)

        run_id = await create_inspector_run(version_id)

        # Get content records for version_id
        db_file_nodes = await get_analyzable_nodes_by_version_id(
            version_id, {DbNodeKind.CODEBASE_FILE}
        )

        db_all_codebase_nodes = await get_analyzable_nodes_by_version_id(
            version_id, {DbNodeKind.CODEBASE_FILE, DbNodeKind.CODEBASE_DIRECTORY}
        )

        # Get content records for previous_version_id if available
        if previous_version is not None:
            db_previous_file_nodes = await get_analyzable_nodes_by_version_id(
                previous_version_id, {DbNodeKind.CODEBASE_FILE}
            )
        # Download s3 for version_id (and previous if available)
        s3_client = boto3.client(
            "s3", endpoint_url=os.environ.get("AWS_S3_ENDPOINT_URL")
        )
        with (
            tempfile.TemporaryDirectory() as download_dir,
            tempfile.TemporaryDirectory() as previous_download_dir,
        ):
            download_root = Path(download_dir)
            if (
                version.status == VersionStatus.CONNECTED
                or version.status == VersionStatus.GENERATING
            ):
                # TODO: check usage before switching to generating
                # if it's in the connected state, must upload the individual files to S3
                download_archive_key = (
                    f"{version.primary_asset_id}/{version_id}/{version_id}_source.zip"
                )
                download_path = Path(download_dir) / f"{version_id}.zip"
                print(f"downloading zip to {download_path}")
                metadata = s3_client.head_object(
                    Bucket=org_hashed_id, Key=download_archive_key
                )
                install_id = metadata["Metadata"].get("install_id")
                s3_client.download_file(
                    org_hashed_id, download_archive_key, download_path
                )

                extracted_path = unpack_archive_to_finalized_path(
                    archive_path=download_path,
                    extraction_root=Path(download_dir),
                    override_codebase_name=codebase_name,
                )
                print(f"Extracted archive to {extracted_path}")

                db_node_paths = {node.relative_path for node in db_file_nodes}
                file_paths = process_and_upload_all_files_in_parallel(
                    s3_client=s3_client,
                    org_hashed_id=org_hashed_id,
                    primary_asset_id=version.primary_asset_id,
                    version_id=version_id,
                    extracted_path=extracted_path,
                    download_dir=download_dir,
                    db_node_paths=db_node_paths,
                    max_workers=10,
                )

                if version.status == VersionStatus.CONNECTED:
                    set_codebase_status(version_id, VersionStatus.GENERATING)
            else:
                print("Downloading all source files for codebase from s3...")
                file_paths = download_all_source_files_in_parallel(
                    s3_client=s3_client,
                    bucket_name=org_hashed_id,
                    primary_asset_id=str(version.primary_asset.id),
                    version_id=str(version_id),
                    node_rel_paths=[node.relative_path for node in db_file_nodes],
                    download_root=download_root,
                    max_workers=8,
                )
                install_id = None  # TODO: install id is attached to the zip, and is not available on rerun/resume
                # NOTE: can still achieve PR of docs by running export_tech_docs_to_zip manually with install_id via local entrypoint
                print("Download complete")

            codebase_dag: FileTreeDag = build_dag(
                root_path=download_root, file_paths=file_paths
            )

            print("======= Nodes from current codebase processed =======")
            for node in codebase_dag.topological_sort():
                print(node.root_rel_path, node.status)

            if previous_version is not None:
                previous_download_root = Path(previous_download_dir)
                print("Downloading all source files for previous codebase from s3...")
                previous_file_paths = download_all_source_files_in_parallel(
                    s3_client=s3_client,
                    bucket_name=org_hashed_id,
                    primary_asset_id=str(previous_version.primary_asset.id),
                    version_id=str(previous_version.id),
                    node_rel_paths=[
                        prev_node.relative_path for prev_node in db_previous_file_nodes
                    ],
                    download_root=previous_download_root,
                    max_workers=8,
                )
                db_all_codebase_prev_version_nodes = (
                    await get_analyzable_nodes_by_version_id(
                        previous_version.id,
                        {DbNodeKind.CODEBASE_FILE, DbNodeKind.CODEBASE_DIRECTORY},
                    )
                )
                print("Download complete for new version of code")

                previous_codebase_dag: FileTreeDag = build_dag(
                    root_path=previous_download_root,
                    file_paths=previous_file_paths,
                )
                print("======= Nodes from previous codebase =======")
                for node in previous_codebase_dag.topological_sort():
                    print(node.root_rel_path, node.status)

                diff_dag = codebase_dag.compute_diff(
                    previous_codebase_dag, delete_file_nodes=False
                )
                print("Diff dag computed")

                print("======= Nodes from diff dag =======")
                for node in diff_dag.topological_sort():
                    print(node.root_rel_path, node.status)

                print("======= Computing diff size in bytes =======")
                changed_nodes = diff_dag.topological_sort(
                    changed_nodes_only=True, files_only=True
                )
                try:
                    # @andrew: We calculate the diff size in bytes, log it while not turning on billing for code diffs
                    compute_and_log_code_diff_size_in_bytes(
                        CodeDiffParams(
                            codebase_name=codebase_name,
                            version_id=str(version.id),
                            primary_asset_id=str(version.primary_asset_id),
                            org_id=org_id,
                            previous_download_root=previous_download_root,
                            download_root=download_root,
                            changed_nodes=changed_nodes,
                        )
                    )
                except InsufficientBalanceError as ibe:
                    print(
                        f"Insufficient balance for org {org_id} to process codebase {codebase_name} {ibe}"
                    )
                    set_codebase_status_in_container.remote(
                        version_id, VersionStatus.INSUFFICIENT_BALANCE.value
                    )
                    # I chose to return here vs re-raising the error because it will get caught and swalloed by the outer try/catch
                    return
            if previous_version is not None:
                sorted_nodes = diff_dag.topological_sort()
            else:
                sorted_nodes = codebase_dag.topological_sort()
                db_all_codebase_prev_version_nodes = None
            path_to_db_node_id = {
                Path(db_node.relative_path): db_node.id
                for db_node in db_all_codebase_nodes
            }
            changes_detected = False  # export tech docs only if changes detected
            print("======= Nodes being processed  =======")
            for node in sorted_nodes:
                if not changes_detected and node.status != NodeStatus.UNMODIFIED:
                    changes_detected = True
                print(node.root_rel_path, node.status, node.kind)

            if previous_version is not None and not changes_detected:
                # Delete the version and return
                await delete_version_by_id(version_id)
                print(
                    f"No modified nodes found for version {version_id}. Deleting version."
                )
                return

            nodes_with_id: list[tuple[Node, uuid.UUID | None]] = [
                (node, path_to_db_node_id[node.root_rel_path])
                for node in sorted_nodes
                if node.root_rel_path != Path(".") and node.status != NodeStatus.REMOVED
            ]
            prev_version_path_to_db_node_id = (
                {
                    Path(db_node.relative_path): db_node.id
                    for db_node in db_all_codebase_prev_version_nodes
                }
                if db_all_codebase_prev_version_nodes
                else {}
            )

            print("======= Nodes with source content id =======")
            for node, sc_id in nodes_with_id:
                print(node.root_rel_path, sc_id)

            await inspect_files(
                version_id=version_id,
                codebase_root=download_root,
                nodes_with_id=nodes_with_id,
                codebase_name=codebase_name,
                run_id=run_id,
                result_loading_config=result_loading_config,
                rel_path_to_previous_version_db_node_ids=prev_version_path_to_db_node_id,
            )
    except Exception as e:
        exception_type = type(e).__name__
        exc_tb = e.__traceback__
        filename = exc_tb.tb_frame.f_code.co_filename
        line_number = exc_tb.tb_lineno
        exception_details = (
            f"Exception type: {exception_type}\nFile: {filename}\nLine: {line_number}"
        )
        send_exception_email.remote(exception_details)
        print(f"Error while processing version {version_id}: {e}")
        set_codebase_status_in_container.remote(version_id, "GENERATION_ERROR")
        raise
    else:
        set_codebase_status_in_container.remote(version_id, "GENERATION_COMPLETE")
        if previous_version is None or changes_detected:
            print("Changes detected exporting tech docs to zip...")
            export_tech_docs_to_zip.remote(version_id, install_id)
        else:
            print("No changes detected skipping tech doc export.")
        try:
            cleanup_old_versions.remote(version_id)
        except Exception as e:
            print(f"Error while cleaning up old versions: {e}")
            raise


def hash_file(file_path: Path) -> str:
    hasher = hashlib.sha256()
    with file_path.open("rb") as file:
        for chunk in iter(lambda: file.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def build_dag(root_path: Path, file_paths: list[Path]) -> FileTreeDag:
    print("Building DAG...")
    dag = FileTreeDag(root_abs_path=root_path)
    for p in file_paths:
        if p.is_file():
            dag.add_file(p, change_status=False, file_hash=hash_file(p))
    return dag


async def inspect_files(
    version_id: uuid.UUID,
    codebase_root: Path,
    nodes_with_id: list[tuple[Node, uuid.UUID | None]],
    codebase_name: str,
    run_id: UUID,
    result_loading_config: list[tuple[UUID, set[NodeStatus]]] | None,
    rel_path_to_previous_version_db_node_ids: dict[Path, uuid.UUID],
) -> None:
    from utils.db import get_all_derived_content_by_node_id

    print("---------- All nodes ----------")

    for node, _ in nodes_with_id:
        print(node)

    # c_files = [
    #     codebase_root / node.root_rel_path
    #     for node, _ in nodes_with_id
    #     if node.root_rel_path.suffix.lower() in [".c"]
    # ]
    # h_files = [
    #     codebase_root / node.root_rel_path
    #     for node, _ in nodes_with_id
    #     if node.root_rel_path.suffix.lower() in [".h"]
    # ]
    # c_and_h_files = c_files + h_files

    # if any(c_files):
    #     index = build_c_project_index(c_and_h_files, codebase_root / codebase_name)
    #     print("C symbol index built")
    #     # Build index here put as single dict key. This is obviously not prod ready. We would ideally name the dict
    #     # by unique id (or ephemeral) and pass in a dict handle  the downstream functions that need shared data
    #     d = modal.Dict.from_name("temp", create_if_missing=True)
    #     d["symbol_table"] = index

    tasks = []
    c_symbol_table_task = CSymbolTableTask(
        root_node=nodes_with_id[-1][0],
        task_name="CSymbolTableTask",
        codebase_name=codebase_name,
        codebase_root=codebase_root,
        nodes_relative_paths=[
            node.root_rel_path
            for node, _ in nodes_with_id
            if node.kind == NodeKind.FILE
        ],
    )
    tasks.append(c_symbol_table_task)
    for node, db_node_id in nodes_with_id:
        lite_node = node.into_lite_node()

        if node.kind in {NodeKind.SUB_FOLDER, NodeKind.ROOT_FOLDER}:
            child_doc_tasks = tuple(
                {
                    t
                    for t in tasks
                    if isinstance(t, FileTechDocTask | FolderTechDocTask)
                    and t.node.root_rel_path.as_posix() in node.children
                }
            )
            if node.root_rel_path in rel_path_to_previous_version_db_node_ids:
                prev_db_node_id = rel_path_to_previous_version_db_node_ids[
                    node.root_rel_path
                ]
                prev_folder_derived_contents = await get_all_derived_content_by_node_id(
                    prev_db_node_id
                )
                previous_contents = {
                    dc.content_kind: dc.content for dc in prev_folder_derived_contents
                }
            else:
                previous_contents = None
            folder_tech_docs_task = FolderTechDocTask(
                node=lite_node,
                task_name=f"FolderTechDoc {node.root_rel_path}",
                child_docs_tasks=child_doc_tasks,
                codebase_name=codebase_name,
                db_node_id=db_node_id,
                previous_content=previous_contents,
            )
            folder_embedding_task = EmbeddingTask(
                node=node,
                task_name=f"Embedding TechDoc (Folder) {node.root_rel_path}",
                dependent_tasks=[folder_tech_docs_task],
            )
            tasks.extend([folder_tech_docs_task, folder_embedding_task])
        else:  # File
            source_code = get_file_content(codebase_root / lite_node.root_rel_path)
            source_file_embedding_task = EmbeddingTask(
                node=node,
                task_name=f"Embedding Source Code {node.root_rel_path}",
                source_code=source_code,
                db_node_id=db_node_id,
                dependent_tasks=[c_symbol_table_task],
            )
            file_tech_docs_task = FileTechDocTask(
                codebase_name=codebase_name,
                source_code=source_code,
                node=lite_node,
                task_name=f"TechDoc {node.root_rel_path}",
                db_node_id=db_node_id,
                symbol_table_task=c_symbol_table_task,
                thread_pool=TECH_DOC_THREAD_POOL,
            )
            file_tech_docs_embedding_task = EmbeddingTask(
                node=node,
                task_name=f"Embedding TechDoc (File) {node.root_rel_path}",
                source_code=None,
                db_node_id=None,
                dependent_tasks=[file_tech_docs_task],
            )
            symbols_task = SymbolsTask(
                task_name=f"Symbols {node.root_rel_path}",
                node=lite_node,
                source_code=source_code,
                tech_docs_task=file_tech_docs_task,
                db_node_id=db_node_id,
            )
            symbols_embedding_task = EmbeddingTask(
                node=node,
                task_name=f"Embedding Symbols {node.root_rel_path}",
                source_code=None,
                db_node_id=None,
                dependent_tasks=[symbols_task],
            )
            tasks.extend(
                [
                    source_file_embedding_task,
                    file_tech_docs_task,
                    file_tech_docs_embedding_task,
                    symbols_task,
                    symbols_embedding_task,
                ]
            )

    root_node, root_db_node_id = nodes_with_id[-1]

    # TODO check propagation of changes to root node is working properly such that these tasks are appropriatly triggered
    # on rerun case.

    all_tech_docs_tasks = tuple(
        t for t in tasks if isinstance(t, FileTechDocTask | FolderTechDocTask)
    )
    top_level_tech_docs_task = TopLevelDocsTask(
        node=root_node,
        codebase_name=codebase_name,
        ordered_tech_docs_tasks=all_tech_docs_tasks,  # TODO where does source content go here?
        db_node_id=root_db_node_id,
    )

    has_previous_version = (
        root_node.root_rel_path in rel_path_to_previous_version_db_node_ids
    )
    if has_previous_version:
        prev_db_root_node_id = rel_path_to_previous_version_db_node_ids[
            root_node.root_rel_path
        ]
        prev_root_node_derived_contents = await get_all_derived_content_by_node_id(
            prev_db_root_node_id
        )
        previous_root_node_metadata = defaultdict(list)
        for dc in prev_root_node_derived_contents:
            previous_root_node_metadata[dc.content_kind].append(dc.misc_metadata)
    codebase_tagging_task = CodebaseTaggingTask(
        root_node=root_node,
        codebase_name=codebase_name,
        ordered_tech_docs_tasks=all_tech_docs_tasks,
        db_root_node_id=root_db_node_id,
        previous_root_node_metadata=previous_root_node_metadata
        if has_previous_version
        else None,
    )
    top_level_embedding_task = EmbeddingTask(
        node=root_node,
        task_name="Embedding TopLevelDocs",
        dependent_tasks=[top_level_tech_docs_task],
    )
    tasks.extend(
        [top_level_tech_docs_task, top_level_embedding_task, codebase_tagging_task]
    )

    print("\n---------- All tasks ----------")
    for t in tasks:
        print("=> ", t)

    print("\n---------- Running tasks ----------")
    task_manager = TaskManager.with_s3_persistence(
        bucket_name=os.environ["BUCKET_NAME"], tasks=tasks, serial_exe=False
    )

    print(f"Starting inspection with {len(tasks)} tasks")
    await task_manager.run_tasks(run_id, result_loading_config=result_loading_config)

    print(
        f"Inspection completed! Final progress: {task_manager.progress_state.percent_complete:.1f}%"
    )


def get_file_content(path: Path) -> str:
    return Path(path).read_text()


@app.function(
    image=modal.Image.debian_slim(python_version="3.12")
    .add_local_dir(local_path="../../driver_db", remote_path="/driver_db", copy=True)
    .pip_install("/driver_db")
    .add_local_python_source(
        "common",
        "database",
        "inspection",
        "modal_funcs",
        "onboarding",
        "shared",
        "tasks",
        "utils",
        copy=True,
        ignore=lambda p: False,
    ),
    secrets=[
        modal.Secret.from_name("db"),
    ],
    proxy=modal.Proxy.from_name("my-proxy")
    if os.environ["MODAL_ENVIRONMENT"] in ["dev", "staging", "prod"]
    else None,
)
def set_codebase_status_in_container(version_id: str, status: str) -> None:
    """This container is needed because the local entrypoint can't run using remote packages/secrets"""

    from database.db import engine
    from database.models import Version
    from database.models_enums import VersionStatus
    from sqlmodel import Session

    with Session(engine) as session, session.begin():
        version = session.get(Version, version_id)
        version.status = VersionStatus(status)
        session.add(version)


@app.function(
    image=modal.Image.debian_slim(python_version="3.12")
    .add_local_dir(local_path="../../driver_db", remote_path="/driver_db", copy=True)
    .pip_install("/driver_db")
    .add_local_python_source(
        "common",
        "database",
        "inspection",
        "modal_funcs",
        "onboarding",
        "shared",
        "tasks",
        "utils",
        copy=True,
        ignore=lambda p: False,
    ),
    secrets=[
        modal.Secret.from_name("db"),
    ],
    timeout=3600 * 12,
    proxy=modal.Proxy.from_name("my-proxy")
    if os.environ["MODAL_ENVIRONMENT"] in ["dev", "staging", "prod"]
    else None,
)
def cleanup_old_versions(new_version_id: str) -> None:
    from database.db import engine
    from database.models import DocumentSource, Node, Version
    from sqlmodel import Session, select

    with Session(engine) as session, session.begin():
        # Get all versions
        primary_asset_id = session.get(Version, new_version_id).primary_asset_id
        versions = session.exec(
            select(Version).where(Version.primary_asset_id == primary_asset_id)
        ).all()
        versions_with_sources = session.exec(
            select(Version)
            .join(Node)
            .join(DocumentSource, DocumentSource.source_node_id == Node.id)
            .where(Version.primary_asset_id == primary_asset_id)
        ).all()
        # Sort versions by creation date or any other criteria if needed
        versions_to_keep = sorted(versions, key=lambda v: v.created_at, reverse=True)[
            :10
        ]
        versions_to_keep.extend(versions_with_sources)

        # Remove duplicates from versions_to_keep
        versions_to_keep = list({v.id: v for v in versions_to_keep}.values())

        # Delete all versions except the 10 most recent
        print(f"DEBUG: Keeping {len(versions_to_keep)} unique versions")
        print(f"DEBUG: Deleting {len(versions) - len(versions_to_keep)} versions")

        versions_to_delete = [v for v in versions if v not in versions_to_keep]
        for version in versions_to_keep:
            print(
                f"DEBUG: KEEPING version: {version.id} which was created at {version.created_at}"
            )
        for version in versions_to_delete:
            print(
                f"DEBUG: DELETING version: {version.id} which was created at {version.created_at} (deletion is not implemented yet)"
            )
            session.delete(version)
        session.commit()


@app.local_entrypoint()
def main(
    version_id: str,
    mode: str,
) -> None:
    """Resume or rerun inspector given a version"""
    inspection_mode = InspectionMode.from_str(mode)
    try:
        inspect_db.remote(
            version_id,
            inspection_mode,
        )
    except Exception as e:
        print(f"Error while processing version {version_id}: {e}")
        set_codebase_status_in_container.remote(version_id, "GENERATION_ERROR")
        raise
    else:
        set_codebase_status_in_container.remote(version_id, "GENERATION_COMPLETE")


@app.local_entrypoint()
def test_connection() -> None:
    from onboarding.onboard import run_codebase_connection

    presigned_url = "https://production-codebase-dropzone.s3.us-east-1.amazonaws.com/assets/7803d76b1b1ad91910acc568ecb0bdf8a17d320a8ef12161767147b0a492fb9/8b89be39-8889-4816-ab9e-8de28f3a26c4/cf79eed5-3d1d-4303-9860-18b276486e11/goat.zip?response-content-disposition=inline&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Security-Token=IQoJb3JpZ2luX2VjECIaCXVzLWVhc3QtMSJGMEQCIDSqOs1DOJ%2Ffb1rrTFFBlVBUY1yCuokz6NX2tQYuH95dAiBNBGbqDxAOf5ERXCVCjz3XKjxoy7yeONsmA%2FsAlRD6kSq%2BBAj7%2F%2F%2F%2F%2F%2F%2F%2F%2F%2F8BEAAaDDg5NjcyNDkwNzExNCIMaHA%2Ffn%2BoIjI0Hbh7KpIE0qbwQr73LuGUxiTopwUniQ3ZjzroZBoPZoWjMbMPneQrKec4eVkK3HrEqBOC6pGZx9J%2BE28UuOVJIlrPMWR5sz9ZFDJgP62%2Fo32zDy0%2FvYs%2F3oH22qUSqPJm6EAWsgvzlUG5fpymFmG2dsb%2BSy4jEoWNj32Ln9vs7VQiBfazk1KvKjdBwefTOTYXtHO0kMOiZnLkpCPI%2Fb2r406tPmC4OkyKWRQ58TjkZWl9HZz41r%2BhkdrjeFh6Zi3eoxHtK7h2kMf0DxGT7NedpmRnIGJaJGvppfTMCV%2B6iHVXmHdYDFWwwrSZB7cBas8liL7Y3XtHMGgVC54%2BpMD2qbnL6K%2F8LSAzSvdyRiFnavd5jlskB3%2FtxlkTELwns9X2ldTKSJvZ5niS%2B6nO7oYR%2BTNr6tnLIRtHgSnnuzjMWTfhFgrPDIcTenM47WkBor%2FU%2FT1UMs7Gnbz0cMA7gHcTb4ndqgI29vZOkoDSonNd5L%2Fk0AJCcEFP%2BmAi8xpSux1AiD3GNkZttyKdQ3kNbEUZ754wzzgOSsP2SNxqpu3rwBKhrCp65Rnsh6phgCtHYLoqExxiG9p3sNPFBdf3AOV3yaRcOolDilSO0yWUdpEtvAH80YniTSizeVTmhsHFTgoeE1Vpp4f%2F4Gc4Q2UzYBTJmU6IzddD0T6sPq1To%2B%2Bq74sTjSC7OHtzsil28vxWrCmLgIGqDN1%2FzzEw9%2FqtwgY6xgLXsz%2F3KY2IJxs3OOXS3DWdapj7ZFg9gAtyAVswuqxJDwTHYdYpNFElIA0AGJkN7n1ynb8%2BzYqUsvQ9Qur9TLV9APh5K%2FAXPIPm9PNC4tUSQSfj3El%2BTVVp4SHRtpKyI0E22KGmxQ2K7XcgS8OmvoCFPNTIZZotlYVZO1DZqsOwDrmrZ%2FGx%2FVUEiGg%2Fu08gJ0i9E6vAQk%2FWACksuXnxyuShMy1YaeCLH4PZ3RarEBKmIcBQ%2FbkQJHx3qFH%2BPsAl2apUY4ZKQcdC27L%2FwL7VuRwVBZenMfI0duU8UEf%2B8%2BqFvjwM5iTAE%2B1eUV6ZWcUShCqAzptYFKT4EbWeds1l5sJFYWGdil%2FoDh%2BqxQRf1R%2B3g8jKBovflY8t5GZjfNJ0arA%2FeIqk%2Fk9VNDwnvT874sfhYPMQZpjtgvSKMMTLVU7hDWPAfn%2BfcA%3D%3D&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=ASIA5BSHYGRVOUWEEAZ7%2F20250613%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20250613T012353Z&X-Amz-Expires=3600&X-Amz-SignedHeaders=host&X-Amz-Signature=87f9ec3051be00be6263a93e998f0e099bda48cb2101785dc52b477c5c220cd8"
    provisional_codebase_name = "goat"
    org_id = "org_1CupxiUE3hxtOMwB"
    provider = "manual"
    version_id = "cf79eed5-3d1d-4303-9860-18b276486e11"

    run_codebase_connection.remote(
        presigned_url=presigned_url,
        provisional_codebase_name=provisional_codebase_name,
        org_id=org_id,
        provider=provider,
        version_id=version_id,
    )


@app.local_entrypoint()
def test_cleanup_old_versions(
    version_id: str,
) -> None:
    cleanup_old_versions.remote(version_id)


@app.local_entrypoint()
def test_export(
    version_id: str,
    install_id: str | None = None,
) -> None:
    """Export tech docs to zip"""
    from modal_funcs import export_tech_docs_to_zip

    export_tech_docs_to_zip.remote(version_id, install_id)


@app.local_entrypoint()
def test_inspect_db() -> None:
    version_str = "db0b396f-8902-4325-98f4-b92dfb44b679"
    inspect_db.remote(version_str)


@app.local_entrypoint()
def run_connect_unconnected_repos() -> None:
    connect_unconnected_repos.remote()


@app.function(
    image=modal.Image.debian_slim(python_version="3.12")
    .pip_install("sendgrid", "strawberry-graphql")
    .add_local_python_source(
        "common",
        "database",
        "inspection",
        "modal_funcs",
        "onboarding",
        "shared",
        "tasks",
        "utils",
        copy=True,
        ignore=lambda p: False,
    ),
    secrets=[modal.Secret.from_name("sendgrid"), modal.Secret.from_name("env-name")],
)
def send_exception_email(exception_details: str) -> None:
    import sendgrid
    from sendgrid.helpers.mail import Content, Email, Mail, To

    env_name = os.environ.get("ENV_NAME")
    sendgrid_api_key = os.environ.get("SENDGRID_API_KEY")

    sg = sendgrid.SendGridAPIClient(api_key=sendgrid_api_key)
    from_email = Email("support@driverai.com")  # Replace with your email
    to_email = To("support@driverai.com")  # Replace with recipient's email
    subject = f"MODAL {env_name}: Exception Occurred"
    content = Content("text/plain", f"An exception occurred: {exception_details}")
    mail = Mail(from_email, to_email, subject, content)

    try:
        response = sg.send(mail)
        print(f"Email sent: {response.status_code}")
    except Exception as e:
        print(f"Error sending email: {e}")
