import os
import pprint
import uuid
from dataclasses import dataclass
from pathlib import Path

import modal
from common import app
from tasks import FileTechDocTask, FolderTechDocTask, SymbolsTask, TopLevelDocsTask
from utils.dag import FileTreeDag, Node, NodeKind
from utils.task import TaskManager, flatten_tasks

# TODO considering using concurrent inputs when we're just calling open AI. This should
# save some cost (though costs are negligible today)

# TODO add tasks for embedding, db persistence, etc. We want to be optionally coupled to a db
# so we can run without the full application context, potentially


# Unified structure for file paths and source content IDs
@dataclass
class FileInfo:
    path: Path
    source_content_id: None | uuid.UUID = None


# @app.function(
#     image=modal.Image.debian_slim(python_version="3.12")
#     .pip_install(["boto3", "openai"])
#     .copy_local_dir(
#         local_path=LOCAL_CODEBASE_ROOT, remote_path=REMOTE_CODEBASE_ROOT
#     ),  # TODO this is a hack for testing
#     secrets=[modal.Secret.from_name("aws-inspector-s3")],
#     memory="2048",
#     timeout=3600 * 5,
# )
# async def inspect_local(path: str, run_id: str, resume: bool = False):
#     root_path = Path(path)
#     file_paths = [FileInfo(path=p) for p in root_path.rglob("*") if p.is_file()]
#     codebase_name = root_path.name
#     await inspect_files(file_paths, codebase_name, run_id, resume)


@app.function(
    image=modal.Image.debian_slim(python_version="3.12")
    .copy_local_dir(local_path="../../driver_db", remote_path="/root/driver_db")
    .copy_local_dir(local_path="../../packages/shared", remote_path="/root/shared")
    .pip_install(["boto3", "openai", "tiktoken", "/root/driver_db"]),
    secrets=[
        modal.Secret.from_name("db"),
        modal.Secret.from_name("aws-inspector-s3"),
    ],  # TODO change to god mode credentials
    mounts=[
        modal.Mount.from_local_dir(
            local_path="../../driver_db/certs",
            remote_path="/root/data/",
        ),
    ],
    proxy=modal.Proxy.from_name("pg-proxy"),
    memory="2048",
    timeout=3600 * 5,
    region="us-east",
    concurrency_limit=5,
)
async def inspect_db(codebase_id: uuid.UUID, run_id: str, resume: bool = False):
    import tempfile

    import boto3
    from utils.db import (
        SourceContentTypeMap,
        download_source_content_file,
        get_codebase_by_id,
        get_source_contents_by_codebase_id,
    )

    codebase = await get_codebase_by_id(codebase_id)
    source_contents_files = await get_source_contents_by_codebase_id(
        codebase_id, {SourceContentTypeMap.FILE}
    )
    source_contents_all = await get_source_contents_by_codebase_id(
        codebase_id, {SourceContentTypeMap.FILE, SourceContentTypeMap.DIRECTORY}
    )
    source_content_codebase = await get_source_contents_by_codebase_id(
        codebase_id, {SourceContentTypeMap.CODEBASE_ROOT}
    )
    assert len(source_content_codebase) == 1
    source_content_codebase_id = source_content_codebase[0].id

    # TODO handle the S3_ENDPOINT_URL gracefully
    s3_client = boto3.client("s3", endpoint_url=os.environ.get("AWS_S3_ENDPOINT_URL"))
    with tempfile.TemporaryDirectory() as download_dir:
        download_root = Path(download_dir)
        file_paths = []
        for sc in source_contents_files:
            download_abs_path = download_source_content_file(
                s3_client=s3_client,
                codebase_storage_url=codebase.storage_url,
                codebase_root=codebase.resource_root,
                source_content_rel_path=sc.relative_path,
                download_root=download_root,
            )
            file_paths.append(download_abs_path)
            # file_paths.append(
            #     FileInfo(path=download_abs_path, source_content_id=sc.id)
            # )
        codebase_dag: FileTreeDag = build_dag(
            root_path=download_root, file_paths=file_paths
        )
        sorted_nodes = codebase_dag.topological_sort()
        path_to_source_content_id = {
            Path(sc.relative_path): sc.id for sc in source_contents_all
        }

        for k in path_to_source_content_id.keys():
            print(k)
        print("=======")
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
                    for t in flatten_tasks(tasks)
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
            tasks.append(folder_tech_docs_task)
        else:  # File
            source_code = get_file_content(codebase_root / lite_node.root_rel_path)
            tech_docs_task = FileTechDocTask(
                codebase_name=codebase_name,  # TODO make sure codebase name is handled correctly.
                source_code=source_code,
                node=lite_node,
                task_name=f"TechDoc {node.root_rel_path}",
                source_content_id=sc_id,
            )
            symbols_task = SymbolsTask(
                task_name=f"Symbols {node.root_rel_path}",
                codebase_root=None,
                node=lite_node,
                source_code=source_code,
                tech_docs_task=tech_docs_task,
                source_content_id=sc_id,
            )
            tasks.append(symbols_task)

    all_tech_docs_tasks = tuple(
        t
        for t in flatten_tasks(tasks)
        if (isinstance(t, FileTechDocTask) or isinstance(t, FolderTechDocTask))
    )
    top_level_tech_docs_task = TopLevelDocsTask(
        codebase_name=codebase_name,
        ordered_tech_docs_tasks=all_tech_docs_tasks,  # TODO where does source content go here?
        source_content_id=sc_codebase_id,
    )
    tasks.append(top_level_tech_docs_task)

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
            case _:
                raise ValueError(f"Unknown task type: {t}")


def get_file_content(path: Path) -> str:
    return Path(path).read_text()


#
# @app.function(
#     image=modal.Image.debian_slim(python_version="3.12")
#     .pip_install(["boto3", "openai"])
#     .copy_local_dir(
#         local_path=LOCAL_CODEBASE_ROOT, remote_path=REMOTE_CODEBASE_ROOT
#     ),  # TODO this is a hack for testing
#     secrets=[modal.Secret.from_name("aws-inspector-s3")],
#     memory="2048",  # This gives us room to for all the source code to live in memory and is hopefully conservative.
# )
# async def inspect(root_path, run_id: str, resume: bool = False):
#     print(f"Inspecting {root_path}, run_id: {run_id}")
#     codebase_name = root_path.name
#     # This is sync, not async, but we can block the event loop since we aren't running anything concurrent yet.
#     dag: FileTreeDag = build_dag(root_path)
#     sorted_nodes = dag.topological_sort()
#
#     print("---------- All nodes ----------")
#     for node in sorted_nodes:
#         print(node)
#
#     tasks = []
#     for node in sorted_nodes:
#         lite_node = node.into_lite_node()
#
#         if node.kind in {NodeKind.SUB_FOLDER, NodeKind.ROOT_FOLDER}:
#             # TODO: we need to reconsider the hashing. We should be able to check membership, but the types
#             # are different (on purpose). We don't want to send child info across the wire.
#             # Perhaps the task can convert the node to a lite node instead.
#             # Then we can check membership exactly
#             # TODO revisit this flattening. Feels non-ideal.
#             child_doc_tasks = tuple(
#                 {
#                     t
#                     for t in flatten_tasks(tasks)
#                     if (
#                         isinstance(t, FileTechDocTask)
#                         or isinstance(t, FolderTechDocTask)
#                     )
#                     and t.node.root_rel_path.as_posix() in node.children
#                 }
#             )
#             folder_tech_docs_task = FolderTechDocTask(
#                 node=lite_node,
#                 task_name=f"FolderTechDoc {node.root_rel_path}",
#                 child_docs_tasks=child_doc_tasks,
#                 codebase_name=codebase_name,
#             )
#             tasks.append(folder_tech_docs_task)
#         else:  # File
#             # TODO consider reading source code in the task to save memory for large codebases
#             # Source code could be put in a modal volume up front and cleaned up in a final clean up task
#             source_code = (root_path / node.root_rel_path).read_text()
#             tech_docs_task = FileTechDocTask(
#                 codebase_name=codebase_name,
#                 source_code=source_code,
#                 node=lite_node,
#                 task_name=f"TechDoc {node.root_rel_path}",
#             )
#             symbols_task = SymbolsTask(
#                 task_name=f"Symbols {node.root_rel_path}",
#                 codebase_root=root_path,
#                 node=lite_node,
#                 source_code=source_code,
#                 tech_docs_task=tech_docs_task,
#             )
#             tasks.append(symbols_task)
#
#     all_tech_docs_tasks = tuple(
#         t
#         for t in flatten_tasks(tasks)
#         if (isinstance(t, FileTechDocTask) or isinstance(t, FolderTechDocTask))
#     )
#     top_level_tech_docs_task = TopLevelDocsTask(
#         codebase_name=codebase_name, ordered_tech_docs_tasks=all_tech_docs_tasks
#     )
#     tasks.append(top_level_tech_docs_task)
#
#     print("\n---------- All tasks ----------")
#     for t in tasks:
#         print("=> ", t)
#         # print(hash(t))
#
#     print("\n---------- Running tasks ----------")
#     task_manager = TaskManager(tasks, serial_exe=False)
#
#     task_results = await task_manager.run_tasks(run_id, resume=resume)
#
#     print("\n---------- Task results ----------")
#     pprinter = pprint.PrettyPrinter(indent=2)
#     for t, r in task_results.items():
#         print(f"\n==> Task: {t.task_name} Result")
#         match t:
#             case FileTechDocTask():
#                 print(r.result["docs"]["short"]["single_paragraph"])
#             case FolderTechDocTask():
#                 print(r.result["docs"]["short"]["single_sentence"])
#             case SymbolsTask():
#                 pprinter.pprint(r.result["symbols"][:1])
#             case TopLevelDocsTask():
#                 print(r.result["docs"]["short"])
#             case _:
#                 raise ValueError(f"Unknown task type: {t}")


@app.function(
    image=modal.Image.debian_slim(python_version="3.12")
    .copy_local_dir(local_path="../../driver_db", remote_path="/root/driver_db")
    .pip_install(["boto3", "openai", "/root/driver_db"]),
    secrets=[modal.Secret.from_name("db")],
    mounts=[
        modal.Mount.from_local_dir(
            local_path="../../driver_db/certs",
            remote_path="/root/data/",
        ),
    ],
    proxy=modal.Proxy.from_name("pg-proxy"),
)
async def db_test():
    from database.db import async_engine
    from database.models_v1 import Codebase
    from sqlmodel import select
    from sqlmodel.ext.asyncio.session import AsyncSession

    async with AsyncSession(async_engine) as session:
        codebases = await session.exec(select(Codebase).limit(2))
        print("Codebases: ", codebases.all())


@app.local_entrypoint()
def main(resume_from_id: str | None = None):
    # from dotenv import load_dotenv
    # load_dotenv()

    if resume_from_id:
        resume = True
        run_id = resume_from_id
    else:
        resume = False
        run_id = uuid.uuid4()  # When rerunning we would supply this. This is used to identify the run in the db
    try:
        # inspect_local.remote(REMOTE_CODEBASE_ROOT, str(run_id), resume=resume)
        inspect_db.remote(
            uuid.UUID("4e50214d-d05d-4d5f-8313-78b3dd674fba"), run_id, resume=resume
        )
        # asyncio.run(inspect_db.local(uuid.UUID("8dc2ecd9-1289-4359-90a3-dacdd42405a7"), run_id, resume=resume))
    finally:
        print("Run id: ", run_id)
