import hashlib
import os
import pprint
import uuid
from dataclasses import dataclass
from pathlib import Path

import modal
from common import app
from tasks import (
    EmbeddingTask,
    FileTechDocTask,
    FolderTechDocTask,
    SymbolsTask,
    TopLevelDocsTask,
)
from utils.dag import FileTreeDag, Node, NodeKind, NodeStatus
from utils.task import TaskManager

# TODO considering using concurrent inputs when we're just calling open AI. This should
# save some cost (though costs are negligible today)


# Unified structure for file paths and source content IDs
@dataclass
class FileInfo:
    path: Path
    source_content_id: None | uuid.UUID = None


@app.function(
    image=modal.Image.debian_slim(python_version="3.12")
    .copy_local_dir(local_path="../../driver_db", remote_path="/driver_db")
    .copy_local_dir(local_path="../../packages/shared", remote_path="/shared_pkg")
    .pip_install(
        ["boto3", "openai>=1.40.2", "pydantic>=2.8.2", "tiktoken", "/shared_pkg"]
    ),
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
    run_id: str,
    resume: bool = False,
    rerun_node_paths: list[str] | None = None,
    new_codebase_id: uuid.UUID | None = None,
) -> None:
    if new_codebase_id:
        assert (
            rerun_node_paths is None
        ), "Cannot rerun specific nodes when doing diff update flow"

    import tempfile

    import boto3
    from utils.db import (
        SourceContentTypeMap,
        download_source_content_file,
        get_analyzable_source_contents_by_codebase_id,
        get_codebase_by_id,
    )

    codebase = await get_codebase_by_id(codebase_id)
    source_contents_files = await get_analyzable_source_contents_by_codebase_id(
        codebase_id, {SourceContentTypeMap.FILE}
    )
    source_contents_all = await get_analyzable_source_contents_by_codebase_id(
        codebase_id, {SourceContentTypeMap.FILE, SourceContentTypeMap.DIRECTORY}
    )
    source_content_codebase = await get_analyzable_source_contents_by_codebase_id(
        codebase_id, {SourceContentTypeMap.CODEBASE_ROOT}
    )
    assert len(source_content_codebase) == 1
    source_content_codebase_id = source_content_codebase[0].id

    # Get the new stuff if applicable
    if new_codebase_id:
        new_codebase = await get_codebase_by_id(new_codebase_id)
        new_source_contents_files = await get_analyzable_source_contents_by_codebase_id(
            new_codebase_id, {SourceContentTypeMap.FILE}
        )
        new_source_contents_all = await get_analyzable_source_contents_by_codebase_id(
            new_codebase_id, {SourceContentTypeMap.FILE, SourceContentTypeMap.DIRECTORY}
        )
        new_source_content_codebase = (
            await get_analyzable_source_contents_by_codebase_id(
                new_codebase_id, {SourceContentTypeMap.CODEBASE_ROOT}
            )
        )
        assert len(new_source_content_codebase) == 1
        new_source_content_codebase_id = new_source_content_codebase[0].id

    # TODO handle the S3_ENDPOINT_URL gracefully
    s3_client = boto3.client("s3", endpoint_url=os.environ.get("AWS_S3_ENDPOINT_URL"))
    with (
        tempfile.TemporaryDirectory() as download_dir,
        tempfile.TemporaryDirectory() as new_download_dir,
    ):
        download_root = Path(download_dir)
        file_paths = []
        print("Downloading all source files for codebase from s3...")
        for sc in source_contents_files:
            download_abs_path = download_source_content_file(
                s3_client=s3_client,
                codebase_storage_url=codebase.storage_url,
                codebase_root=codebase.resource_root,
                source_content_rel_path=sc.relative_path,
                download_root=download_root,
            )
            file_paths.append(download_abs_path)
        print("Download complete")

        def change_root_with_first_component(
            original_root: Path | str, additional_path: Path | str
        ) -> tuple[Path, str]:
            original_root_path = Path(original_root)
            additional_path_path = Path(additional_path)

            relative_path = additional_path_path.relative_to(original_root_path)
            first_component = relative_path.parts[0]
            new_root = original_root_path / first_component

            return new_root, first_component

        # We must build the dags with the codebase name removed so dags can be properly diffed. (Codebase name changes with version right now)
        codebase_root_with_cb_name_inc, cb_name_old = change_root_with_first_component(
            download_root, file_paths[0]
        )
        codebase_dag: FileTreeDag = build_dag(
            root_path=codebase_root_with_cb_name_inc, file_paths=file_paths
        )

        print("======= Nodes from original codebase processed =======")
        for node in codebase_dag.topological_sort():
            print(node.root_rel_path, node.status)

        if new_codebase_id:
            new_download_root = Path(new_download_dir)
            new_file_paths = []
            print("Downloading all source files for new codebase from s3...")
            for scn in new_source_contents_files:
                download_abs_path = download_source_content_file(
                    s3_client=s3_client,
                    codebase_storage_url=new_codebase.storage_url,
                    codebase_root=new_codebase.resource_root,
                    source_content_rel_path=scn.relative_path,
                    download_root=new_download_root,
                )
                new_file_paths.append(download_abs_path)
            print("Download complete for new version of code")

            (
                new_codebase_root_with_cb_name_inc,
                cb_name_new,
            ) = change_root_with_first_component(new_download_root, new_file_paths[0])
            new_codebase_dag: FileTreeDag = build_dag(
                root_path=new_codebase_root_with_cb_name_inc, file_paths=new_file_paths
            )
            print("======= Nodes from new codebase =======")
            for node in new_codebase_dag.topological_sort():
                print(node.root_rel_path, node.status)

            diff_dag = new_codebase_dag.compute_diff(codebase_dag)
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
            if new_codebase_id:
                sorted_nodes = diff_dag.topological_sort()
                path_to_source_content_id = {
                    Path(sc.relative_path): sc.id for sc in new_source_contents_all
                }
                cb_name = cb_name_new
            else:
                sorted_nodes = codebase_dag.topological_sort()
                path_to_source_content_id = {
                    Path(sc.relative_path): sc.id for sc in source_contents_all
                }
                cb_name = cb_name_old

        print("======= Nodes being processed  =======")
        for node in sorted_nodes:
            print(node.root_rel_path, node.status)

        nodes_with_id: list[tuple[Node, uuid.UUID | None]] = [
            (node, path_to_source_content_id[Path(cb_name) / node.root_rel_path])
            for node in sorted_nodes
        ]

        print("======= Nodes with source content id =======")
        for node, sc_id in nodes_with_id:
            print(node.root_rel_path, sc_id)

        await inspect_files(
            sc_codebase_id=new_source_content_codebase_id
            if new_codebase_id
            else source_content_codebase_id,
            codebase_root=new_codebase_root_with_cb_name_inc
            if new_codebase_id
            else codebase_root_with_cb_name_inc,
            nodes_with_id=nodes_with_id,
            codebase_name=codebase.codebase_name,  # We're passing in the old codebase name for consistency with old cb docs.
            run_id=run_id,
            resume=resume,
            is_rerun=bool(rerun_node_paths),
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
    codebase_root: Path,
    nodes_with_id: list[tuple[Node, uuid.UUID | None]],
    codebase_name: str,
    run_id: str,
    resume: bool,
    is_rerun: bool,
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
                task_name=f"FolderTechDoc {node.root_rel_path}",
                child_docs_tasks=child_doc_tasks,
                codebase_name=codebase_name,
                source_content_id=sc_id,
                load_persisted_results=load_persisted_results,
            )
            folder_embedding_task = EmbeddingTask(
                task_name=f"Embedding TechDoc (Folder) {node.root_rel_path}",
                dependent_tasks=[folder_tech_docs_task],
                load_persisted_results=load_persisted_results,
            )
            tasks.extend([folder_tech_docs_task, folder_embedding_task])
        else:  # File
            source_code = get_file_content(codebase_root / lite_node.root_rel_path)
            source_file_embedding_task = EmbeddingTask(
                task_name=f"Embedding Source Code {node.root_rel_path}",
                source_code=source_code,
                source_content_id=sc_id,
                dependent_tasks=[],
                load_persisted_results=load_persisted_results,
            )
            file_tech_docs_task = FileTechDocTask(
                codebase_name=codebase_name,
                source_code=source_code,
                node=lite_node,
                task_name=f"TechDoc {node.root_rel_path}",
                source_content_id=sc_id,
                load_persisted_results=load_persisted_results,
            )
            file_tech_docs_embedding_task = EmbeddingTask(
                task_name=f"Embedding TechDoc (File) {node.root_rel_path}",
                source_code=None,
                source_content_id=None,
                dependent_tasks=[file_tech_docs_task],
                load_persisted_results=load_persisted_results,
            )
            symbols_task = SymbolsTask(
                task_name=f"Symbols {node.root_rel_path}",
                node=lite_node,
                source_code=source_code,
                tech_docs_task=file_tech_docs_task,
                source_content_id=sc_id,
                load_persisted_results=load_persisted_results,
            )
            symbols_embedding_task = EmbeddingTask(
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
        # TODO when not rerrunning, we should always have the root node as the last. VERIFY!
        root_node, _ = nodes_with_id[-1]

        # If no changes propagated to the root node due to child changes/additions/deletions,
        # we can reuse the persisted result for the tasks
        load_persisted_results = root_node.status == NodeStatus.UNMODIFIED

        all_tech_docs_tasks = tuple(
            t for t in tasks if isinstance(t, FileTechDocTask | FolderTechDocTask)
        )
        top_level_tech_docs_task = TopLevelDocsTask(
            codebase_name=codebase_name,
            ordered_tech_docs_tasks=all_tech_docs_tasks,  # TODO where does source content go here?
            source_content_id=sc_codebase_id,
            load_persisted_results=load_persisted_results,
        )
        top_level_embedding_task = EmbeddingTask(
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

    task_results = await task_manager.run_tasks(run_id, resume=resume)

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


@app.local_entrypoint()
def main(
    codebase_id: str, resume_from_id: str | None = None, rerun_paths: str | None = None
) -> None:
    print("Processing codebase with id: ", codebase_id)

    rerun_node_paths = (
        rerun_paths.split(",") if rerun_paths and rerun_paths.strip() else None
    )
    if rerun_node_paths:
        print("Rerunning nodes:")
        rerun_node_paths = [path.lstrip("/") for path in rerun_node_paths]
        for path in rerun_node_paths:
            print("--> ", path)

    if resume_from_id:
        resume = True
        run_id = resume_from_id
    else:
        resume = False
        run_id = uuid.uuid4()  # When rerunning we would supply this. This is used to identify the run in the db
    try:
        inspect_db.remote(
            uuid.UUID(codebase_id),
            run_id,
            resume=resume,
            rerun_node_paths=rerun_node_paths,
        )
    finally:
        print("Run id: ", run_id)


@app.local_entrypoint()
def diff_flow() -> None:
    codebase_id = "73fcda74-7c0b-4911-9ff8-9d09f1cac654"
    existing_codebase_id = "43acca23-f561-46d6-8387-2e09a34d8b93"
    run_id = "d947cc38-c20e-4c63-85cb-0f21c83e9d86"

    print("Onboarding complete for codebase: ", codebase_id)
    inspect_db.remote(
        existing_codebase_id,
        run_id,
        True,
        None,
        codebase_id,
    )

    print("Diff flow complete for codebase: ", codebase_id)
