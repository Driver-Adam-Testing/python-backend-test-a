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
from utils.dag import FileTreeDag, Node, NodeKind
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
    proxy=modal.Proxy.from_name("pg-proxy"),
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
):
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

    # TODO handle the S3_ENDPOINT_URL gracefully
    s3_client = boto3.client("s3", endpoint_url=os.environ.get("AWS_S3_ENDPOINT_URL"))
    with tempfile.TemporaryDirectory() as download_dir:
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

        codebase_dag: FileTreeDag = build_dag(
            root_path=download_root, file_paths=file_paths
        )

        if rerun_node_paths:
            for rerun_path in rerun_node_paths:
                rerun_path = download_root / rerun_path
                codebase_dag.mark_as_modified(
                    rerun_path, include_upstream=False, include_downstream=True
                )

        if rerun_node_paths:
            sorted_nodes = codebase_dag.topological_sort(changed_nodes_only=True)
        else:
            sorted_nodes = codebase_dag.topological_sort()

        path_to_source_content_id = {
            Path(sc.relative_path): sc.id for sc in source_contents_all
        }

        print("======= Paths being processed =======")
        for node in sorted_nodes:
            print(node.root_rel_path)

        nodes_with_id: list[tuple[Node, uuid.UUID | None]] = [
            (node, path_to_source_content_id[node.root_rel_path])
            for node in sorted_nodes
            if node.root_rel_path != Path(".")
        ]

        await inspect_files(
            sc_codebase_id=source_content_codebase_id,
            codebase_root=download_root,
            nodes_with_id=nodes_with_id,
            codebase_name=codebase.codebase_name,
            run_id=run_id,
            resume=resume,
            is_rerun=bool(rerun_node_paths),
        )


def build_dag(root_path: Path, file_paths: list[Path]) -> FileTreeDag:
    print("Building DAG...")
    dag = FileTreeDag(root_abs_path=root_path)
    for p in file_paths:
        if p.is_file():
            dag.add_file(p, change_status=False)
    return dag


async def inspect_files(
    sc_codebase_id: uuid.UUID,
    codebase_root: Path,
    nodes_with_id: list[tuple[Node, uuid.UUID | None]],
    codebase_name: str,
    run_id: str,
    resume: bool,
    is_rerun: bool,
):
    print("---------- All nodes ----------")
    for node, _ in nodes_with_id:
        print(node)

    tasks = []
    for node, sc_id in nodes_with_id:
        lite_node = node.into_lite_node()

        if node.kind in {NodeKind.SUB_FOLDER, NodeKind.ROOT_FOLDER}:
            child_doc_tasks = tuple(
                {
                    t
                    for t in tasks
                    if (
                        isinstance(t, FileTechDocTask)
                        or isinstance(t, FolderTechDocTask)
                    )
                    and t.node.root_rel_path.as_posix() in node.children
                }
            )
            folder_tech_docs_task = FolderTechDocTask(
                node=lite_node,
                task_name=f"FolderTechDoc {node.root_rel_path}",
                child_docs_tasks=child_doc_tasks,
                codebase_name=codebase_name,
                source_content_id=sc_id,
            )
            folder_embedding_task = EmbeddingTask(
                task_name=f"Embedding TechDoc (Folder) {node.root_rel_path}",
                dependent_tasks=[folder_tech_docs_task],
            )
            tasks.extend([folder_tech_docs_task, folder_embedding_task])
        else:  # File
            source_code = get_file_content(codebase_root / lite_node.root_rel_path)
            source_file_embedding_task = EmbeddingTask(
                task_name=f"Embedding Source Code {node.root_rel_path}",
                source_code=source_code,
                source_content_id=sc_id,
                dependent_tasks=[],
            )
            file_tech_docs_task = FileTechDocTask(
                codebase_name=codebase_name,
                source_code=source_code,
                node=lite_node,
                task_name=f"TechDoc {node.root_rel_path}",
                source_content_id=sc_id,
            )
            file_tech_docs_embedding_task = EmbeddingTask(
                task_name=f"Embedding TechDoc (File) {node.root_rel_path}",
                source_code=None,
                source_content_id=None,
                dependent_tasks=[file_tech_docs_task],
            )
            symbols_task = SymbolsTask(
                task_name=f"Symbols {node.root_rel_path}",
                node=lite_node,
                source_code=source_code,
                tech_docs_task=file_tech_docs_task,
                source_content_id=sc_id,
            )
            symbols_embedding_task = EmbeddingTask(
                task_name=f"Embedding Symbols {node.root_rel_path}",
                source_code=None,
                source_content_id=None,
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

    if not is_rerun:
        # We never update top level docs in a rerun where specific nodes have been specified for simplicity.
        all_tech_docs_tasks = tuple(
            t
            for t in tasks
            if (isinstance(t, FileTechDocTask) or isinstance(t, FolderTechDocTask))
        )
        top_level_tech_docs_task = TopLevelDocsTask(
            codebase_name=codebase_name,
            ordered_tech_docs_tasks=all_tech_docs_tasks,  # TODO where does source content go here?
            source_content_id=sc_codebase_id,
        )
        top_level_embedding_task = EmbeddingTask(
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
):
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
