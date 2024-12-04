import hashlib
import os
import pprint
import uuid
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

import modal
from onboarding.onboard import run_codebase_onboarding

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
        ]
    )
)

from common import app  # noqa: E402
from utils.dag import FileTreeDag, Node, NodeKind, NodeStatus  # noqa: E402

with inspection_image.imports():
    from database.models_v1 import Enum_Derived_Content_Status
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


# Unified structure for file paths and source content IDs
@dataclass
class FileInfo:
    path: Path
    source_content_id: None | uuid.UUID = None


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
    codebase_id: uuid.UUID,
    version_id: uuid.UUID,
    workspace_id: uuid.UUID,
    resume: bool = False,  # TODO: think about resume functionality with previous versions
    rerun_node_paths: list[str] | None = None,
) -> None:
    import tempfile

    import boto3
    from utils.db import (
        SourceContentTypeMap,
        create_inspector_run,
        download_source_content_file,
        get_analyzable_source_contents_by_version_id,
        get_codebase_by_id,
        get_latest_run_from_version_id,
        get_version_by_id,
        get_workspace_by_id,
    )

    workspace = await get_workspace_by_id(workspace_id)
    org_id = workspace.organization_id
    org_hashed_id = hashlib.sha256(org_id.encode()).hexdigest()[:63]

    # Get the Version and check if it has previous_version_id
    version = await get_version_by_id(version_id)
    previous_version_id = version.previous_version_id
    codebase = await get_codebase_by_id(codebase_id)
    codebase_name = codebase.codebase_name

    if previous_version_id:
        assert (
            rerun_node_paths is None
        ), "Cannot rerun specific nodes when doing diff update flow"

    # Create the InspectorRun
    run_id = await create_inspector_run(version_id)
    previous_run_id = (
        await get_latest_run_from_version_id(previous_version_id)
        if previous_version_id
        else None
    )

    # Get content records for version_id
    source_contents_files = await get_analyzable_source_contents_by_version_id(
        version_id, {SourceContentTypeMap.FILE}
    )
    source_contents_all = await get_analyzable_source_contents_by_version_id(
        version_id, {SourceContentTypeMap.FILE, SourceContentTypeMap.DIRECTORY}
    )
    source_content_codebase = await get_analyzable_source_contents_by_version_id(
        version_id, {SourceContentTypeMap.CODEBASE_ROOT}
    )
    assert len(source_content_codebase) == 1
    source_content_codebase_id = source_content_codebase[0].id

    # Get content recrods for previous_version_id if available
    if previous_version_id:
        previous_source_contents_files = (
            await get_analyzable_source_contents_by_version_id(
                previous_version_id, {SourceContentTypeMap.FILE}
            )
        )

    # Download s3 for version_id (and previous if avaialble)
    s3_client = boto3.client("s3", endpoint_url=os.environ.get("AWS_S3_ENDPOINT_URL"))
    with (
        tempfile.TemporaryDirectory() as download_dir,
        tempfile.TemporaryDirectory() as previous_download_dir,
    ):
        download_root = Path(download_dir)
        file_paths = []
        print("Downloading all source files for codebase from s3...")
        for sc in source_contents_files:
            download_abs_path = download_source_content_file(
                s3_client=s3_client,
                bucket_name=org_hashed_id,
                codebase_id=codebase_id,
                version_id=version_id,
                source_content_rel_path=sc.relative_path,
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

        if previous_version_id:
            previous_download_root = Path(previous_download_dir)
            previous_file_paths = []
            print("Downloading all source files for previous codebase from s3...")
            for scn in previous_source_contents_files:
                download_abs_path = download_source_content_file(
                    s3_client=s3_client,
                    bucket_name=org_hashed_id,
                    codebase_id=codebase_id,
                    version_id=previous_version_id,
                    source_content_rel_path=scn.relative_path,
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

        if rerun_node_paths:
            for rerun_path in rerun_node_paths:
                rerun_path = download_root / rerun_path
                codebase_dag.mark_as_modified(
                    rerun_path, include_upstream=False, include_downstream=True
                )

        if rerun_node_paths:
            sorted_nodes = codebase_dag.topological_sort(changed_nodes_only=True)
        else:
            if previous_version_id:
                sorted_nodes = diff_dag.topological_sort()
            else:
                sorted_nodes = codebase_dag.topological_sort()
        path_to_source_content_id = {
            Path(sc.relative_path): sc.id for sc in source_contents_all
        }

        print("======= Nodes being processed  =======")
        for node in sorted_nodes:
            print(node.root_rel_path, node.status, node.kind)

        nodes_with_id: list[tuple[Node, uuid.UUID | None]] = [
            (node, path_to_source_content_id[node.root_rel_path])
            for node in sorted_nodes
            if node.root_rel_path != Path(".")
        ]

        print("======= Nodes with source content id =======")
        for node, sc_id in nodes_with_id:
            print(node.root_rel_path, sc_id)

        await inspect_files(
            sc_codebase_id=source_content_codebase_id,
            version_id=version_id,
            codebase_root=download_root,
            nodes_with_id=nodes_with_id,
            root_node=sorted_nodes[-1],
            codebase_name=codebase_name,
            run_id=run_id,
            resume=resume,
            is_rerun=bool(rerun_node_paths),
            previous_run_id=previous_run_id,
        )


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
    sc_codebase_id: uuid.UUID,
    version_id: uuid.UUID,
    codebase_root: Path,
    nodes_with_id: list[tuple[Node, uuid.UUID | None]],
    root_node: Node,
    codebase_name: str,
    run_id: str,
    resume: bool,
    is_rerun: bool,
    previous_run_id: str | None = None,
) -> None:
    print("---------- All nodes ----------")
    for node, _ in nodes_with_id:
        print(node)

    tasks = []
    for node, sc_id in nodes_with_id:
        lite_node = node.into_lite_node()

        # TODO check condition below!!
        # When resuming (without diff flow), we should always load persisted results. All nodes are UNMODIFIED in this case.
        # When rerunning, we will have marked nodes to rerun as modified if we want them to be rerun, so we don't want to load results for those marked as modified.
        # When diffing, we should load persisted results for nodes that are unmodified, and not for nodes that are modified.
        load_persisted_results = lite_node.status == NodeStatus.UNMODIFIED

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
                version_id=version_id,
                task_name=f"FolderTechDoc {node.root_rel_path}",
                child_docs_tasks=child_doc_tasks,
                codebase_name=codebase_name,
                source_content_id=sc_id,
                load_persisted_results=load_persisted_results,
            )
            folder_embedding_task = EmbeddingTask(
                node=node,
                task_name=f"Embedding TechDoc (Folder) {node.root_rel_path}",
                dependent_tasks=[folder_tech_docs_task],
                load_persisted_results=load_persisted_results,
            )
            tasks.extend([folder_tech_docs_task, folder_embedding_task])
        else:  # File
            source_code = get_file_content(codebase_root / lite_node.root_rel_path)
            source_file_embedding_task = EmbeddingTask(
                node=node,
                task_name=f"Embedding Source Code {node.root_rel_path}",
                source_code=source_code,
                source_content_id=sc_id,
                dependent_tasks=[],
                load_persisted_results=load_persisted_results,
            )
            file_tech_docs_task = FileTechDocTask(
                codebase_name=codebase_name,
                version_id=version_id,
                source_code=source_code,
                node=lite_node,
                task_name=f"TechDoc {node.root_rel_path}",
                source_content_id=sc_id,
                load_persisted_results=load_persisted_results,
            )
            file_tech_docs_embedding_task = EmbeddingTask(
                node=node,
                task_name=f"Embedding TechDoc (File) {node.root_rel_path}",
                source_code=None,
                source_content_id=None,
                dependent_tasks=[file_tech_docs_task],
                load_persisted_results=load_persisted_results,
            )
            symbols_task = SymbolsTask(
                task_name=f"Symbols {node.root_rel_path}",
                version_id=version_id,
                node=lite_node,
                source_code=source_code,
                tech_docs_task=file_tech_docs_task,
                source_content_id=sc_id,
                load_persisted_results=load_persisted_results,
            )
            symbols_embedding_task = EmbeddingTask(
                node=node,
                task_name=f"Embedding Symbols {node.root_rel_path}",
                source_code=None,
                source_content_id=None,
                dependent_tasks=[symbols_task],
                load_persisted_results=load_persisted_results,
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

    # We never generate top level docs in a re-run scenario since we don't have the full task result graph
    # in order to update them.
    if not is_rerun:
        # # TODO when not rerrunning, we should always have the root node as the last. VERIFY!
        # root_node, _ = nodes_with_id[-1]

        # If no changes propagated to the root node due to child changes/additions/deletions,
        # we can reuse the persisted result for the tasks
        load_persisted_results = root_node.status == NodeStatus.UNMODIFIED

        all_tech_docs_tasks = tuple(
            t for t in tasks if isinstance(t, FileTechDocTask | FolderTechDocTask)
        )
        top_level_tech_docs_task = TopLevelDocsTask(
            node=root_node,
            version_id=version_id,
            codebase_name=codebase_name,
            ordered_tech_docs_tasks=all_tech_docs_tasks,  # TODO where does source content go here?
            source_content_id=sc_codebase_id,
            load_persisted_results=load_persisted_results,
        )
        top_level_embedding_task = EmbeddingTask(
            node=root_node,
            task_name="Embedding TopLevelDocs",
            dependent_tasks=[top_level_tech_docs_task],
            load_persisted_results=load_persisted_results,
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
        run_id, resume=resume, previous_run_id=previous_run_id
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


# TODO resurrect rerun
# @app.local_entrypoint()
# def main(
#     codebase_id: str, resume_from_id: str | None = None, rerun_paths: str | None = None
# ) -> None:
#     print("Processing codebase with id: ", codebase_id)
#
#     rerun_node_paths = (
#         rerun_paths.split(",") if rerun_paths and rerun_paths.strip() else None
#     )
#     if rerun_node_paths:
#         print("Rerunning nodes:")
#         rerun_node_paths = [path.lstrip("/") for path in rerun_node_paths]
#         for path in rerun_node_paths:
#             print("--> ", path)
#
#     if resume_from_id:
#         resume = True
#         run_id = resume_from_id
#     else:
#         resume = False
#         run_id = uuid.uuid4()  # When rerunning we would supply this. This is used to identify the run in the db
#     try:
#         inspect_db.remote(
#             uuid.UUID(codebase_id),
#             run_id,
#             resume=resume,
#             rerun_node_paths=rerun_node_paths,
#         )
#     finally:
#         print("Run id: ", run_id)


@app.function(
    image=modal.Image.debian_slim(python_version="3.12").pip_install("sendgrid"),
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
)


@app.function(
    image=onboarding_and_inspect_image,
    secrets=[
        modal.Secret.from_name("db"),
    ],
    mounts=[
        modal.Mount.from_local_dir(
            local_path="../../driver_db/certs",
            remote_path="/root/data/",
        ),
        modal.Mount.from_local_python_packages("onboarding"),  # Why not automounted?
    ],
    proxy=modal.Proxy.from_name("pg-proxy")
    if os.environ["MODAL_ENVIRONMENT"] != "staging"
    else None,
    timeout=3600 * 8,
    region="us-east",
    concurrency_limit=5,
    keep_warm=1,
)
def onboard_and_inspect(
    presigned_url: str,
    archive_name: str,
    org_id: str,
    creator_id: str,
    workspace_id: UUID,
    provider: str = "manual",
    version: str | None = None,
) -> None:
    from onboarding.onboard_utils import set_codebase_status

    print(
        f"Onboarding for: {archive_name} from {provider} with org_id: {org_id}, creator_id: {creator_id}, "
        f"workspace_id: {workspace_id} with presigned_url: {presigned_url}, version: {version}"
    )
    try:
        codebase_id, version_id = run_codebase_onboarding.remote(
            presigned_url,
            archive_name,
            org_id,
            creator_id,
            workspace_id,
            provider,
            version=version,
        )
        print(f"Onboarding complete for codebase: {codebase_id}, {version_id}")
        print("Inspecting...")
        inspect_db.remote(codebase_id, version_id, workspace_id)
        print("Inspection complete")

        set_codebase_status(
            codebase_id, Enum_Derived_Content_Status.generation_complete
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
        # Since codebase could possibly be undefined in this clean up action, we don't care if it fails
        with suppress(Exception):
            set_codebase_status(
                codebase_id, Enum_Derived_Content_Status.generation_error
            )
        raise e


# @app.local_entrypoint()
# def inspect_from_repo(public_repo_url: str, commit_sha: str) -> None:
#     # Hardcoded to driver default for now
#     workspace_id = UUID("32de9990-b63d-4e8e-9567-58e2a78292ec")
#     codebase_id, version_id = run_codebase_onboarding.remote(
#         public_repo_url, commit_sha, workspace_id
#     )
#     inspect_db.remote(codebase_id, version_id, workspace_id) # TODO: must put the path fix in before merge!!!!!!!!!

# @app.local_entrypoint()
# def main()
