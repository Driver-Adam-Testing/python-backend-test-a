import hashlib
import os
import pprint
import uuid
from enum import Enum
from pathlib import Path
from uuid import UUID

import modal
from onboarding.onboard import (
    connect_unconnected_repos,
    handle_github_events,
    run_codebase_connection,
)

inspection_image = (
    modal.Image.debian_slim(python_version="3.12")
    .copy_local_dir(local_path="../../driver_db", remote_path="/driver_db")
    .copy_local_dir(local_path="../../packages/shared", remote_path="/shared_pkg")
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
        ]
    )
)

from common import app  # noqa: E402
from utils.dag import FileTreeDag, Node, NodeKind, NodeStatus  # noqa: E402

with inspection_image.imports():
    from tasks import (
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
    mounts=[
        modal.Mount.from_local_dir(
            local_path="../../driver_db/certs",
            remote_path="/root/data/",
        ),
    ],
    proxy=modal.Proxy.from_name("pg-proxy")
    if os.environ["MODAL_ENVIRONMENT"] != "staging"
    else None,
    memory="2048",
    timeout=3600 * 8,
    region="us-east",
    concurrency_limit=5,
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
        reencode_file,
        set_codebase_status,
        unpack_archive,
    )
    from utils.db import (
        create_inspector_run,
        download_source_file,
        get_analyzable_nodes_by_version_id,
        get_version_by_id,
        try_get_prev_version,
    )

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
            file_paths = []
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

                extracted_path = unpack_archive(
                    archive_path=download_path,
                    override_codebase_name=codebase_name,
                    extraction_path=download_dir,
                )
                print(f"Extracted archive to {extracted_path}")
                for root, _, files in os.walk(extracted_path):
                    for filename in files:
                        local_path = Path(root) / filename
                        trimmed_path = local_path.relative_to(download_dir)
                        for node in db_file_nodes:
                            if node.relative_path == str(trimmed_path):
                                reencode_file(local_path)

                                s3_client.upload_file(
                                    local_path,
                                    org_hashed_id,
                                    f"{version.primary_asset_id}/{version_id}/{node.relative_path}",
                                )
                                print(
                                    f"uploading {trimmed_path} to s3 at {version.primary_asset_id}/{version_id}/{node.relative_path}"
                                )
                                file_paths.append(local_path)
                if version.status == VersionStatus.CONNECTED:
                    set_codebase_status(version_id, VersionStatus.GENERATING)

            else:
                print("Downloading all source files for codebase from s3...")
                for db_file_node in db_file_nodes:
                    download_abs_path = download_source_file(
                        s3_client=s3_client,
                        bucket_name=org_hashed_id,
                        primary_asset_id=str(version.primary_asset.id),
                        version_id=str(version_id),
                        node_rel_path=db_file_node.relative_path,
                        download_root=download_root,
                    )
                    file_paths.append(download_abs_path)
                print("Download complete")

            codebase_dag: FileTreeDag = build_dag(
                root_path=download_root, file_paths=file_paths
            )

            print("======= Nodes from current codebase processed =======")
            for node in codebase_dag.topological_sort():
                print(node.root_rel_path, node.status)

            if previous_version is not None:
                previous_download_root = Path(previous_download_dir)
                previous_file_paths = []
                print("Downloading all source files for previous codebase from s3...")
                for db_previous_file_node in db_previous_file_nodes:
                    download_abs_path = download_source_file(
                        s3_client=s3_client,
                        bucket_name=org_hashed_id,
                        primary_asset_id=str(previous_version.primary_asset.id),
                        version_id=str(previous_version.id),
                        node_rel_path=db_previous_file_node.relative_path,
                        download_root=previous_download_root,
                    )
                    previous_file_paths.append(download_abs_path)
                print("Download complete for new version of code")

                previous_codebase_dag: FileTreeDag = build_dag(
                    root_path=previous_download_root,
                    file_paths=previous_file_paths,
                )
                print("======= Nodes from previous codebase =======")
                for node in previous_codebase_dag.topological_sort():
                    print(node.root_rel_path, node.status)

                diff_dag = codebase_dag.compute_diff(previous_codebase_dag)
                print("Diff dag computed")

                print("======= Nodes from diff dag =======")
                for node in diff_dag.topological_sort():
                    print(node.root_rel_path, node.status)

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
                if node.root_rel_path != Path(".")
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

    tasks = []
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
                dependent_tasks=[],
            )
            file_tech_docs_task = FileTechDocTask(
                codebase_name=codebase_name,
                source_code=source_code,
                node=lite_node,
                task_name=f"TechDoc {node.root_rel_path}",
                db_node_id=db_node_id,
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

    task_results = await task_manager.run_tasks(
        run_id, result_loading_config=result_loading_config
    )

    print("\n---------- Task results ----------")
    pprinter = pprint.PrettyPrinter(indent=2)
    for t, r in task_results.items():
        print(f"\n==> Task: {t.task_name} Result")
        match t:
            case FileTechDocTask():
                print(r.result)
                print(r.result["docs"]["short"]["single_paragraph"])
            case FolderTechDocTask():
                print(r.result["docs"]["short"]["single_sentence"])
            case SymbolsTask():
                print(r.result)
                pprinter.pprint(r.result["symbols"][:1])
            case TopLevelDocsTask():
                print(r.result["docs"]["short"])
            case EmbeddingTask():
                print("N/A")
            case _:
                raise ValueError(f"Unknown task type: {t}")


def get_file_content(path: Path) -> str:
    return Path(path).read_text()


@app.function(
    image=modal.Image.debian_slim(python_version="3.12")
    .copy_local_dir(local_path="../../driver_db", remote_path="/driver_db")
    .pip_install("/driver_db"),
    secrets=[
        modal.Secret.from_name("db"),
    ],
    proxy=modal.Proxy.from_name("pg-proxy")
    if os.environ["MODAL_ENVIRONMENT"] != "staging"
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
    image=modal.Image.debian_slim(python_version="3.12").pip_install(
        "sendgrid", "strawberry-graphql"
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
    .copy_local_dir(local_path="../../driver_db", remote_path="/driver_db")
    .pip_install("/driver_db")
    .pip_install("requests")
    .pip_install("boto3")
    .pip_install("gitignore-parser")
    .pip_install("tree-sitter>=0.24.0", "tree-sitter-c>=0.23.4")
)
