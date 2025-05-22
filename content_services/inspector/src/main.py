import hashlib
import os
import uuid
from enum import Enum
from pathlib import Path
from uuid import UUID

import modal
from onboarding.onboard import (
    connect_unconnected_repos,
    handle_github_events,
    handle_gitlab_events,
    run_codebase_connection,
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
            "openai>=1.40.2",
            "pydantic>=2.8.2",
            "tiktoken",
            "/shared_pkg",
            "tree-sitter==0.24.0",
            "tree-sitter-c==0.23.4",
            "gitignore-parser",
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
    )
)

from common import app  # noqa: E402
from utils.dag import FileTreeDag, Node, NodeKind, NodeStatus  # noqa: E402

with inspection_image.imports():
    from tasks import (
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
    proxy=modal.Proxy.from_name("pg-proxy")
    if os.environ["MODAL_ENVIRONMENT"] in ["dev", "prod"]
    else None,
    memory=4096,
    timeout=3600 * 8,
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
    from database.models_v2_enums import NodeKind as DbNodeKind
    from database.models_v2_enums import VersionStatus
    from onboarding.onboard_utils import (
        process_and_upload_all_files_in_parallel,
        set_codebase_status,
        unpack_archive_to_finalized_path,
    )
    from utils.db import (
        create_inspector_run,
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
            path_to_db_node_id = {
                Path(db_node.relative_path): db_node.id
                for db_node in db_all_codebase_nodes
            }

            print("======= Nodes being processed  =======")
            for node in sorted_nodes:
                print(node.root_rel_path, node.status, node.kind)

            nodes_with_id: list[tuple[Node, uuid.UUID | None]] = [
                (node, path_to_db_node_id[node.root_rel_path])
                for node in sorted_nodes
                if node.root_rel_path != Path(".") and node.status != NodeStatus.REMOVED
            ]

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
) -> None:
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
            folder_tech_docs_task = FolderTechDocTask(
                node=lite_node,
                task_name=f"FolderTechDoc {node.root_rel_path}",
                child_docs_tasks=child_doc_tasks,
                codebase_name=codebase_name,
                db_node_id=db_node_id,
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
    top_level_embedding_task = EmbeddingTask(
        node=root_node,
        task_name="Embedding TopLevelDocs",
        dependent_tasks=[top_level_tech_docs_task],
    )
    tasks.extend([top_level_tech_docs_task, top_level_embedding_task])

    print("\n---------- All tasks ----------")
    for t in tasks:
        print("=> ", t)

    print("\n---------- Running tasks ----------")
    task_manager = TaskManager.with_s3_persistence(
        bucket_name=os.environ["BUCKET_NAME"], tasks=tasks, serial_exe=False
    )

    await task_manager.run_tasks(run_id, result_loading_config=result_loading_config)


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
    ),
    secrets=[
        modal.Secret.from_name("db"),
    ],
    proxy=modal.Proxy.from_name("pg-proxy")
    if os.environ["MODAL_ENVIRONMENT"] in ["dev", "prod"]
    else None,
)
def set_codebase_status_in_container(version_id: str, status: str) -> None:
    """This container is needed because the local entrypoint can't run using remote packages/secrets"""
    from database.db import engine
    from database.models_v2 import Version
    from database.models_v2_enums import VersionStatus
    from sqlmodel import Session

    with Session(engine) as session, session.begin():
        version = session.get(Version, version_id)
        version.status = VersionStatus(status)
        session.add(version)


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
def test_handle_github_events() -> None:
    import json

    body = json.loads("""
        {
            "action": "created",
            "installation": {
                "id": 60598324,
                "client_id": "Iv1.2cdbf00b132438f4",
                "account": {
                "login": "ghiotto1",
                "id": 1228798,
                "node_id": "MDQ6VXNlcjEyMjg3OTg=",
                "avatar_url": "https://avatars.githubusercontent.com/u/1228798?v=4",
                "gravatar_id": "",
                "url": "https://api.github.com/users/ghiotto1",
                "html_url": "https://github.com/ghiotto1",
                "followers_url": "https://api.github.com/users/ghiotto1/followers",
                "following_url": "https://api.github.com/users/ghiotto1/following{/other_user}",
                "gists_url": "https://api.github.com/users/ghiotto1/gists{/gist_id}",
                "starred_url": "https://api.github.com/users/ghiotto1/starred{/owner}{/repo}",
                "subscriptions_url": "https://api.github.com/users/ghiotto1/subscriptions",
                "organizations_url": "https://api.github.com/users/ghiotto1/orgs",
                "repos_url": "https://api.github.com/users/ghiotto1/repos",
                "events_url": "https://api.github.com/users/ghiotto1/events{/privacy}",
                "received_events_url": "https://api.github.com/users/ghiotto1/received_events",
                "type": "User",
                "user_view_type": "public",
                "site_admin": false
                },
                "repository_selection": "all",
                "access_tokens_url": "https://api.github.com/app/installations/60597730/access_tokens",
                "repositories_url": "https://api.github.com/installation/repositories",
                "html_url": "https://github.com/settings/installations/60597730",
                "app_id": 869041,
                "app_slug": "driverai-gh-demo",
                "target_id": 1228798,
                "target_type": "User",
                "permissions": {
                "contents": "read",
                "metadata": "read",
                "pull_requests": "read",
                "repository_hooks": "read"
                },
                "events": [
                "create",
                "delete",
                "fork",
                "membership",
                "organization",
                "pull_request",
                "push",
                "repository"
                ],
                "created_at": "2025-02-05T13:30:32.000-08:00",
                "updated_at": "2025-02-05T13:30:33.000-08:00",
                "single_file_name": null,
                "has_multiple_single_files": false,
                "single_file_paths": [

                ],
                "suspended_by": null,
                "suspended_at": null
            },
            "repositories": [
                {
                "id": 10464543,
                "node_id": "MDEwOlJlcG9zaXRvcnkxMDQ2NDU0Mw==",
                "name": "dotfiles",
                "full_name": "ghiotto1/dotfiles",
                "private": false
                },
                {
                "id": 116281345,
                "node_id": "MDEwOlJlcG9zaXRvcnkxMTYyODEzNDU=",
                "name": "spam-detection",
                "full_name": "ghiotto1/spam-detection",
                "private": false
                }
            ],
            "requester": null,
            "sender": {
                "login": "ghiotto1",
                "id": 1228798,
                "node_id": "MDQ6VXNlcjEyMjg3OTg=",
                "avatar_url": "https://avatars.githubusercontent.com/u/1228798?v=4",
                "gravatar_id": "",
                "url": "https://api.github.com/users/ghiotto1",
                "html_url": "https://github.com/ghiotto1",
                "followers_url": "https://api.github.com/users/ghiotto1/followers",
                "following_url": "https://api.github.com/users/ghiotto1/following{/other_user}",
                "gists_url": "https://api.github.com/users/ghiotto1/gists{/gist_id}",
                "starred_url": "https://api.github.com/users/ghiotto1/starred{/owner}{/repo}",
                "subscriptions_url": "https://api.github.com/users/ghiotto1/subscriptions",
                "organizations_url": "https://api.github.com/users/ghiotto1/orgs",
                "repos_url": "https://api.github.com/users/ghiotto1/repos",
                "events_url": "https://api.github.com/users/ghiotto1/events{/privacy}",
                "received_events_url": "https://api.github.com/users/ghiotto1/received_events",
                "type": "User",
                "user_view_type": "public",
                "site_admin": false
            }
            }
    """)

    installation_id = str(body["installation"]["id"])
    repositories = body["repositories"]
    repos_added = []
    repos_deleted = []
    repos_pushed = []
    for repo in repositories:
        repos_added.append(
            {
                "id": repo["id"],
                "name": repo["name"],
                "full_name": repo["full_name"],
            }
        )

    org_id = "org_s76pU1v8LAYhTOWB"

    handle_github_events.remote(
        installation_id,
        org_id,
        repos_added,
        repos_deleted,
        repos_pushed,
    )


@app.local_entrypoint()
def test_handle_gitlab_events() -> None:
    import json

    raw_body = """
    {
        "provider_name": "Gitlab Enterprise Self Managed", "provider_kind": "GITLAB_ENTERPRISE_SELF_MANAGED", "repo_name": "serverless-ness", "org": "onthebeach/sub-group", "last_updated": "2023-11-02T17:48:28.000+01:00", "metadata": {"id": 5, "description": null, "name": "serverless-ness", "name_with_namespace": "onthebeach / sub-group / serverless-ness", "path": "serverless-ness", "path_with_namespace": "onthebeach/sub-group/serverless-ness", "created_at": "2025-01-10T12:16:13.533Z", "default_branch": "master", "tag_list": [], "topics": [], "ssh_url_to_repo": "git@driver-gitlab.ngrok.io:onthebeach/sub-group/serverless-ness.git", "http_url_to_repo": "http://driver-gitlab.ngrok.io/onthebeach/sub-group/serverless-ness.git", "web_url": "http://driver-gitlab.ngrok.io/onthebeach/sub-group/serverless-ness", "readme_url": "http://driver-gitlab.ngrok.io/onthebeach/sub-group/serverless-ness/-/blob/master/README.md", "forks_count": 0, "avatar_url": null, "star_count": 0, "last_activity_at": "2025-01-10T12:16:16.256Z", "namespace": {"id": 43, "name": "sub-group", "path": "sub-group", "kind": "group", "full_path": "onthebeach/sub-group", "parent_id": 36, "avatar_url": null, "web_url": "http://driver-gitlab.ngrok.io/groups/onthebeach/sub-group"}, "_links": {"self": "http://driver-gitlab.ngrok.io/api/v4/projects/5", "issues": "http://driver-gitlab.ngrok.io/api/v4/projects/5/issues", "merge_requests": "http://driver-gitlab.ngrok.io/api/v4/projects/5/merge_requests", "repo_branches": "http://driver-gitlab.ngrok.io/api/v4/projects/5/repository/branches", "labels": "http://driver-gitlab.ngrok.io/api/v4/projects/5/labels", "events": "http://driver-gitlab.ngrok.io/api/v4/projects/5/events", "members": "http://driver-gitlab.ngrok.io/api/v4/projects/5/members", "cluster_agents": "http://driver-gitlab.ngrok.io/api/v4/projects/5/cluster_agents"}, "packages_enabled": true, "empty_repo": false, "archived": false, "visibility": "private", "resolve_outdated_diff_discussions": false, "container_expiration_policy": {"cadence": "1d", "enabled": false, "keep_n": 10, "older_than": "90d", "name_regex": ".*", "name_regex_keep": null, "next_run_at": "2025-01-11T12:16:16.323Z"}, "repository_object_format": "sha1", "issues_enabled": true, "merge_requests_enabled": true, "wiki_enabled": true, "jobs_enabled": true, "snippets_enabled": true, "container_registry_enabled": true, "service_desk_enabled": false, "service_desk_address": null, "can_create_merge_request_in": true, "issues_access_level": "enabled", "repository_access_level": "enabled", "merge_requests_access_level": "enabled", "forking_access_level": "enabled", "wiki_access_level": "enabled", "builds_access_level": "enabled", "snippets_access_level": "enabled", "pages_access_level": "private", "analytics_access_level": "enabled", "container_registry_access_level": "enabled", "security_and_compliance_access_level": "private", "releases_access_level": "enabled", "environments_access_level": "enabled", "feature_flags_access_level": "enabled", "infrastructure_access_level": "enabled", "monitor_access_level": "enabled", "model_experiments_access_level": "enabled", "model_registry_access_level": "enabled", "emails_disabled": false, "emails_enabled": true, "shared_runners_enabled": true, "lfs_enabled": true, "creator_id": 35, "import_url": null, "import_type": "gitlab_project", "import_status": "finished", "import_error": null, "open_issues_count": 0, "description_html": "", "updated_at": "2025-01-10T12:16:18.425Z", "ci_default_git_depth": 20, "ci_forward_deployment_enabled": true, "ci_forward_deployment_rollback_allowed": true, "ci_job_token_scope_enabled": false, "ci_separated_caches": true, "ci_allow_fork_pipelines_to_run_in_parent_project": true, "ci_id_token_sub_claim_components": ["project_path", "ref_type", "ref"], "build_git_strategy": "fetch", "keep_latest_artifact": true, "restrict_user_defined_variables": false, "ci_pipeline_variables_minimum_override_role": "maintainer", "runners_token": "GR1348941ebgdPJxxkjPSppzdxZmP", "runner_token_expiration_interval": null, "group_runners_enabled": true, "auto_cancel_pending_pipelines": "enabled", "build_timeout": 3600, "auto_devops_enabled": true, "auto_devops_deploy_strategy": "continuous", "ci_push_repository_for_job_token_allowed": false, "ci_config_path": null, "public_jobs": true, "shared_with_groups": [], "only_allow_merge_if_pipeline_succeeds": false, "allow_merge_on_skipped_pipeline": null, "request_access_enabled": true, "only_allow_merge_if_all_discussions_are_resolved": false, "remove_source_branch_after_merge": true, "printing_merge_request_link_enabled": true, "merge_method": "merge", "squash_option": "default_off", "enforce_auth_checks_on_uploads": true, "suggestion_commit_message": null, "merge_commit_template": null, "squash_commit_template": null, "issue_branch_template": null, "warn_about_potentially_unwanted_characters": true, "autoclose_referenced_issues": true, "approvals_before_merge": 0, "mirror": false, "external_authorization_classification_label": null, "marked_for_deletion_at": null, "marked_for_deletion_on": null, "requirements_enabled": true, "requirements_access_level": "enabled", "security_and_compliance_enabled": true, "pre_receive_secret_detection_enabled": false, "compliance_frameworks": [], "issues_template": null, "merge_requests_template": null, "ci_restrict_pipeline_cancellation_role": "developer", "merge_pipelines_enabled": false, "merge_trains_enabled": false, "merge_trains_skip_train_allowed": false, "only_allow_merge_if_all_status_checks_passed": false, "allow_pipeline_trigger_approve_deployment": false, "prevent_merge_without_jira_issue": false, "permissions": {"project_access": null, "group_access": {"access_level": 40, "notification_level": 3}}}, "latest_commit": {"repository_url": "http://driver-gitlab.ngrok.io/onthebeach/sub-group/serverless-ness.git", "default_branch": "master", "commit": {"id": "049dfd3cf98b69791c4b22a2438daf0a89a7e98f", "message": "Initialized from 'Serverless Framework/JS' project templateTemplate repository: https://gitlab.com/gitlab-org/project-templates/serverless-frameworkCommit SHA: a2a5b57371d276dcc6f529c71aa2e77d43b4db34", "author": "GitLab", "date": "2023-11-02T17:48:28.000+01:00"}}, "default_branch": "master", "installation_id": "1802a3a5-c387-4631-8710-dbc961f39d8c"
    }
    """
    body = json.loads(raw_body)

    installation_id = str(body["installation_id"])
    repos_added = [body]
    repos_deleted = []
    repos_pushed = []

    org_id = "org_s76pU1v8LAYhTOWB"

    handle_gitlab_events.remote(
        installation_id,
        org_id,
        repos_added,
        repos_deleted,
        repos_pushed,
    )


@app.local_entrypoint()
def local_connect() -> None:
    presigned_url = "https://development-codebase-dropzone.s3.us-east-1.amazonaws.com/codebases/6b00f9ade1094692d388c5dc385d7dccc474504aa5778cb5389f732f36ef641/spam-detection.zip?response-content-disposition=inline&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEDcaCXVzLWVhc3QtMSJHMEUCIDb4lgoSFbgsjOCrn8KqTgEvJCqneR7D%2FLoBicug%2FN8VAiEAxqEgXXbcUAx5QF1dgCBZKM%2Fn3sST6vJEQUpKoLTl%2BEsqtQQITxABGgw1NTAwODI3NjExMDkiDOCQGpznimsTef0tFyqSBLjkfZ44%2FFeWpkDD04jMWokfR1rBPrTU9dBLze%2FNIcI6uHp6Fw60wyQomXxV4Tb3dV7v9GHCRfr97N%2BzsnmxVNt%2FNCjx02HHGa7AiGFqr%2FcLyOWMDmT%2BB%2FXl3yEBwcv4zGeJtKgDt4q%2FnkS9v3PszUAvaBKO8XudD8JM6AaEL1W5LGQ1MQmIRn45gYI4RVA4sUqQOrEFWMgPPdOXoNH%2BDiOaqFdMdLpQuJNEcg7HNyLPb2%2BR6CdkxfYEAuoHXESy8gU4xNPm2ZsDRCsyDfyernHiEKHAY9e%2BxceWUonvhlHWZzdxWEW0djo2fSDO44Q6WvdqDGKFIfJt%2Bexn5dEfij5iScD4ZuKpQAsrxPA9NsUOf%2Fd17OqzTj7mSIchaUaNHpqYVDsFx%2B0ciBAL%2B224TbKZ5Wh3mQ1cCQPmI7YW9Ww7lKRoP44RJt4kZp38oT8sf4adigJ8ZfK%2FHk%2Fv%2BpPtIVA9T%2FQj1ghwXRnECI7ayWf2ttgR%2F3HMz6eDfYkjEiwiG1DLT%2FDUN56jK3srUDkZ2AxXM4eX%2BYBb5jjGc6Idn2zeS%2F%2FOhPoHW%2F%2Fd8g5ZlIjwTGH65CF4%2FHAUSfrn8sH%2B5BmVofxovg%2BQfnYIbsPh2RhaDBbMsBIwe%2FS7T3tOLqotrZZaHHC%2BiYS3e0h89qM99JtrdNaou%2FBpg1vH0h5KB1rucJVZGs%2FmUyDjGOSN4VZnASuXMP27j70GOsUCNX74rhYcMEGe2YvXpi0vfWVque7MXHUOVBHv2XIXsd2DFTxqpzdViHNiusKhpoLx6Pd1i1Z0p%2BPvafxwO3jboHkXf8j3lRpcYpO8A5jyxnXBOp0rkpMt12lm4kjQkk18GGP5klw6fEjnZIf3McPF4CUhX5LVJbwXhagg7f7Cfu6PT8qBkkhpqsMRCy6kqyL8yfaAKhKdg8JZCxFqdr6ZsBxgpNzq3uktJfzy8hgUATqGSsm7qBQUXJUy1hCJ%2B9OYWHlZaGvqxBd3bznWaGfV%2Bx4a95o7z0MRZyw0%2FP1Nzwj%2Fm0j6Q%2FFO9W81zA7T7dLNYP8kc5lp6YsaiX04C1PVeoeI38dcg9DMm71aYS56AVEPSb%2Bf5GmsQtsLt22KYIpI%2F6ph8S%2F9PsDkWsR5xTm1B7cnzKE7PB8bMNGx2zYE2q6v1qSosQ%3D%3D&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=ASIAYAE342GKXYB6FPCY%2F20250205%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20250205T220805Z&X-Amz-Expires=7200&X-Amz-SignedHeaders=host&X-Amz-Signature=942c1c5225bce1d7517927819c71a65dd46f8c48dba33239b12cd193937ca0a4"
    archive_name = "spam-detection.zip"
    org_id = "org_s76pU1v8LAYhTOWB"
    provider = "github"
    version_id = "db0b396f-8902-4325-98f4-b92dfb44b679"

    run_codebase_connection.remote(
        presigned_url,
        archive_name,
        org_id,
        version_id,
        provider,
    )
    # inspect_db.remote(version_id = 'e308eccc-8105-4cd4-8163-c591b507057d')


@app.local_entrypoint()
def github_auth_change() -> None:
    import json

    org_id = "org_s76pU1v8LAYhTOWB"

    remove_event = json.loads("""
    {
        "action": "removed",
        "installation": {
            "id": 60598324,
            "client_id": "Iv1.2cdbf00b132438f4",
            "account": {
            "login": "ghiotto1",
            "id": 1228798,
            "node_id": "MDQ6VXNlcjEyMjg3OTg=",
            "avatar_url": "https://avatars.githubusercontent.com/u/1228798?v=4",
            "gravatar_id": "",
            "url": "https://api.github.com/users/ghiotto1",
            "html_url": "https://github.com/ghiotto1",
            "followers_url": "https://api.github.com/users/ghiotto1/followers",
            "following_url": "https://api.github.com/users/ghiotto1/following{/other_user}",
            "gists_url": "https://api.github.com/users/ghiotto1/gists{/gist_id}",
            "starred_url": "https://api.github.com/users/ghiotto1/starred{/owner}{/repo}",
            "subscriptions_url": "https://api.github.com/users/ghiotto1/subscriptions",
            "organizations_url": "https://api.github.com/users/ghiotto1/orgs",
            "repos_url": "https://api.github.com/users/ghiotto1/repos",
            "events_url": "https://api.github.com/users/ghiotto1/events{/privacy}",
            "received_events_url": "https://api.github.com/users/ghiotto1/received_events",
            "type": "User",
            "user_view_type": "public",
            "site_admin": false
            },
            "repository_selection": "selected",
            "access_tokens_url": "https://api.github.com/app/installations/60597730/access_tokens",
            "repositories_url": "https://api.github.com/installation/repositories",
            "html_url": "https://github.com/settings/installations/60597730",
            "app_id": 869041,
            "app_slug": "driverai-gh-demo",
            "target_id": 1228798,
            "target_type": "User",
            "permissions": {
            "contents": "read",
            "metadata": "read",
            "pull_requests": "read",
            "repository_hooks": "read"
            },
            "events": [
            "create",
            "delete",
            "fork",
            "membership",
            "organization",
            "pull_request",
            "push",
            "repository"
            ],
            "created_at": "2025-02-05T13:30:32.000-08:00",
            "updated_at": "2025-02-05T13:35:25.000-08:00",
            "single_file_name": null,
            "has_multiple_single_files": false,
            "single_file_paths": [

            ],
            "suspended_by": null,
            "suspended_at": null
        },
        "repository_selection": "selected",
        "repositories_added": [

        ],
        "repositories_removed": [
            {
            "id": 10464543,
            "node_id": "MDEwOlJlcG9zaXRvcnkxMDQ2NDU0Mw==",
            "name": "dotfiles",
            "full_name": "ghiotto1/dotfiles",
            "private": false
            }
        ],
        "requester": null,
        "sender": {
            "login": "ghiotto1",
            "id": 1228798,
            "node_id": "MDQ6VXNlcjEyMjg3OTg=",
            "avatar_url": "https://avatars.githubusercontent.com/u/1228798?v=4",
            "gravatar_id": "",
            "url": "https://api.github.com/users/ghiotto1",
            "html_url": "https://github.com/ghiotto1",
            "followers_url": "https://api.github.com/users/ghiotto1/followers",
            "following_url": "https://api.github.com/users/ghiotto1/following{/other_user}",
            "gists_url": "https://api.github.com/users/ghiotto1/gists{/gist_id}",
            "starred_url": "https://api.github.com/users/ghiotto1/starred{/owner}{/repo}",
            "subscriptions_url": "https://api.github.com/users/ghiotto1/subscriptions",
            "organizations_url": "https://api.github.com/users/ghiotto1/orgs",
            "repos_url": "https://api.github.com/users/ghiotto1/repos",
            "events_url": "https://api.github.com/users/ghiotto1/events{/privacy}",
            "received_events_url": "https://api.github.com/users/ghiotto1/received_events",
            "type": "User",
            "user_view_type": "public",
            "site_admin": false
        }
    }
    """)
    add_github_event = json.loads("""
        {
        "action": "added",
        "installation": {
            "id": 60598324,
            "client_id": "Iv1.2cdbf00b132438f4",
            "account": {
            "login": "ghiotto1",
            "id": 1228798,
            "node_id": "MDQ6VXNlcjEyMjg3OTg=",
            "avatar_url": "https://avatars.githubusercontent.com/u/1228798?v=4",
            "gravatar_id": "",
            "url": "https://api.github.com/users/ghiotto1",
            "html_url": "https://github.com/ghiotto1",
            "followers_url": "https://api.github.com/users/ghiotto1/followers",
            "following_url": "https://api.github.com/users/ghiotto1/following{/other_user}",
            "gists_url": "https://api.github.com/users/ghiotto1/gists{/gist_id}",
            "starred_url": "https://api.github.com/users/ghiotto1/starred{/owner}{/repo}",
            "subscriptions_url": "https://api.github.com/users/ghiotto1/subscriptions",
            "organizations_url": "https://api.github.com/users/ghiotto1/orgs",
            "repos_url": "https://api.github.com/users/ghiotto1/repos",
            "events_url": "https://api.github.com/users/ghiotto1/events{/privacy}",
            "received_events_url": "https://api.github.com/users/ghiotto1/received_events",
            "type": "User",
            "user_view_type": "public",
            "site_admin": false
            },
            "repository_selection": "selected",
            "access_tokens_url": "https://api.github.com/app/installations/60597730/access_tokens",
            "repositories_url": "https://api.github.com/installation/repositories",
            "html_url": "https://github.com/settings/installations/60597730",
            "app_id": 869041,
            "app_slug": "driverai-gh-demo",
            "target_id": 1228798,
            "target_type": "User",
            "permissions": {
            "contents": "read",
            "metadata": "read",
            "pull_requests": "read",
            "repository_hooks": "read"
            },
            "events": [
            "create",
            "delete",
            "fork",
            "membership",
            "organization",
            "pull_request",
            "push",
            "repository"
            ],
            "created_at": "2025-02-05T13:30:32.000-08:00",
            "updated_at": "2025-02-05T13:35:25.000-08:00",
            "single_file_name": null,
            "has_multiple_single_files": false,
            "single_file_paths": [

            ],
            "suspended_by": null,
            "suspended_at": null
        },
        "repository_selection": "selected",
        "repositories_added": [
            {
            "id": 116281345,
            "node_id": "MDEwOlJlcG9zaXRvcnkxMTYyODEzNDU=",
            "name": "spam-detection",
            "full_name": "ghiotto1/spam-detection",
            "private": false
            }
        ],
        "repositories_removed": [

        ],
        "requester": null,
        "sender": {
            "login": "ghiotto1",
            "id": 1228798,
            "node_id": "MDQ6VXNlcjEyMjg3OTg=",
            "avatar_url": "https://avatars.githubusercontent.com/u/1228798?v=4",
            "gravatar_id": "",
            "url": "https://api.github.com/users/ghiotto1",
            "html_url": "https://github.com/ghiotto1",
            "followers_url": "https://api.github.com/users/ghiotto1/followers",
            "following_url": "https://api.github.com/users/ghiotto1/following{/other_user}",
            "gists_url": "https://api.github.com/users/ghiotto1/gists{/gist_id}",
            "starred_url": "https://api.github.com/users/ghiotto1/starred{/owner}{/repo}",
            "subscriptions_url": "https://api.github.com/users/ghiotto1/subscriptions",
            "organizations_url": "https://api.github.com/users/ghiotto1/orgs",
            "repos_url": "https://api.github.com/users/ghiotto1/repos",
            "events_url": "https://api.github.com/users/ghiotto1/events{/privacy}",
            "received_events_url": "https://api.github.com/users/ghiotto1/received_events",
            "type": "User",
            "user_view_type": "public",
            "site_admin": false
        }
    }
    """)

    installation_id = str(add_github_event["installation"]["id"])
    org_id = "org_s76pU1v8LAYhTOWB"
    repos_added = []
    repos_removed = []
    for repo in add_github_event["repositories_added"]:
        repos_added.append(
            {
                "id": repo["id"],
                "name": repo["name"],
                "full_name": repo["full_name"],
            }
        )
    for repo in remove_event["repositories_removed"]:
        repos_removed.append(
            {
                "id": repo["id"],
                "name": repo["name"],
                "full_name": repo["full_name"],
            }
        )
    handle_github_events.remote(
        installation_id,
        org_id,
        repos_added,
        repos_removed,
        [],
    )


@app.local_entrypoint()
def github_delete_test() -> None:
    import json

    body = json.loads("""
    {
        "action": "deleted",
        "installation": {
            "id": 60598324,
            "client_id": "Iv1.2cdbf00b132438f4",
            "account": {
            "login": "ghiotto1",
            "id": 1228798,
            "node_id": "MDQ6VXNlcjEyMjg3OTg=",
            "avatar_url": "https://avatars.githubusercontent.com/u/1228798?v=4",
            "gravatar_id": "",
            "url": "https://api.github.com/users/ghiotto1",
            "html_url": "https://github.com/ghiotto1",
            "followers_url": "https://api.github.com/users/ghiotto1/followers",
            "following_url": "https://api.github.com/users/ghiotto1/following{/other_user}",
            "gists_url": "https://api.github.com/users/ghiotto1/gists{/gist_id}",
            "starred_url": "https://api.github.com/users/ghiotto1/starred{/owner}{/repo}",
            "subscriptions_url": "https://api.github.com/users/ghiotto1/subscriptions",
            "organizations_url": "https://api.github.com/users/ghiotto1/orgs",
            "repos_url": "https://api.github.com/users/ghiotto1/repos",
            "events_url": "https://api.github.com/users/ghiotto1/events{/privacy}",
            "received_events_url": "https://api.github.com/users/ghiotto1/received_events",
            "type": "User",
            "user_view_type": "public",
            "site_admin": false
            },
            "repository_selection": "selected",
            "access_tokens_url": "https://api.github.com/app/installations/60597730/access_tokens",
            "repositories_url": "https://api.github.com/installation/repositories",
            "html_url": "https://github.com/settings/installations/60597730",
            "app_id": 869041,
            "app_slug": "driverai-gh-demo",
            "target_id": 1228798,
            "target_type": "User",
            "permissions": {
            "contents": "read",
            "metadata": "read",
            "pull_requests": "read",
            "repository_hooks": "read"
            },
            "events": [
            "create",
            "delete",
            "fork",
            "membership",
            "organization",
            "pull_request",
            "push",
            "repository"
            ],
            "created_at": "2025-02-05T13:30:32.000-08:00",
            "updated_at": "2025-02-05T13:35:25.000-08:00",
            "single_file_name": null,
            "has_multiple_single_files": false,
            "single_file_paths": [

            ],
            "suspended_by": null,
            "suspended_at": null
        },
        "repositories": [
            {
            "id": 116281345,
            "node_id": "MDEwOlJlcG9zaXRvcnkxMTYyODEzNDU=",
            "name": "spam-detection",
            "full_name": "ghiotto1/spam-detection",
            "private": false
            }
        ],
        "sender": {
            "login": "ghiotto1",
            "id": 1228798,
            "node_id": "MDQ6VXNlcjEyMjg3OTg=",
            "avatar_url": "https://avatars.githubusercontent.com/u/1228798?v=4",
            "gravatar_id": "",
            "url": "https://api.github.com/users/ghiotto1",
            "html_url": "https://github.com/ghiotto1",
            "followers_url": "https://api.github.com/users/ghiotto1/followers",
            "following_url": "https://api.github.com/users/ghiotto1/following{/other_user}",
            "gists_url": "https://api.github.com/users/ghiotto1/gists{/gist_id}",
            "starred_url": "https://api.github.com/users/ghiotto1/starred{/owner}{/repo}",
            "subscriptions_url": "https://api.github.com/users/ghiotto1/subscriptions",
            "organizations_url": "https://api.github.com/users/ghiotto1/orgs",
            "repos_url": "https://api.github.com/users/ghiotto1/repos",
            "events_url": "https://api.github.com/users/ghiotto1/events{/privacy}",
            "received_events_url": "https://api.github.com/users/ghiotto1/received_events",
            "type": "User",
            "user_view_type": "public",
            "site_admin": false
        }
    }
    """)
    installation_id = str(body["installation"]["id"])
    org_id = "org_s76pU1v8LAYhTOWB"
    # repos_added = []
    repos_removed = []
    for repo in body["repositories"]:
        repos_removed.append(
            {
                "id": repo["id"],
                "name": repo["name"],
                "full_name": repo["full_name"],
            }
        )

    handle_github_events.remote(
        installation_id,
        org_id,
        [],
        repos_removed,
        [],
    )


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


onboarding_and_inspect_image = (
    modal.Image.debian_slim(python_version="3.12")
    .add_local_dir(local_path="../../driver_db", remote_path="/driver_db", copy=True)
    .pip_install("/driver_db")
    .pip_install("requests")
    .pip_install("boto3")
    .pip_install("gitignore-parser")
    .pip_install("tree-sitter>=0.24.0", "tree-sitter-c>=0.23.4")
)
