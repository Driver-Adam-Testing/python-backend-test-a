from pathlib import Path

import modal

from common import app

from utils.dag import LiteNode
from inspection.files import comprehend_file_top_down

image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install(["openai", "tiktoken"]) # TODO lock versions down
    .apt_install("universal-ctags")
)

function_cfg = dict(secrets=[modal.Secret.from_name("open-ai")], image=image)


@app.function(
    concurrency_limit=8,
    **function_cfg,
)
def make_tech_doc(
    node: LiteNode, source_code: str, codebase_name: str
) -> tuple[bool, dict, LiteNode]:
    from inspection.files import comprehend_file_top_down
    from utils.models import ChatOpenAI

    print(f"Processing tech docs ({node})")
    raise_hard_errors = False
    llm = ChatOpenAI(model="gpt-4o", temperature=0, request_timeout=120)

    file_docs_successful, file_doc = comprehend_file_top_down(
        llm=llm,
        node=node,
        source_code=source_code,
        codebase_name=codebase_name,
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        compression_loop_max_itr=COMPRESSION_LOOP_MAX_ITR,
        max_num_chunks=MAX_NUM_CHUNKS_FILE,
        raise_hard_errors=raise_hard_errors,
    )
    print(f"Tech docs created for ({node})")
    return file_docs_successful, file_doc, node


@app.function(concurrency_limit=3,timeout=60*60, **function_cfg)
def make_symbol_docs(
    node: LiteNode,
    source_code: str,
    file_description_paragraph: str,
    symbol_count_limit: int | None = None,
) -> list[dict[str, any]]:
    from inspection.symbols import document_symbols_in_file

    print(f"Processing symbol docs ({node})")
    symbols = document_symbols_in_file(
        file_node=node,
        source_code=source_code,
        file_description_paragraph=file_description_paragraph,
        symbol_count_limit=symbol_count_limit,
    )
    print(f"Symbol docs created for {node}")
    return symbols


@app.function(concurrency_limit=3, **function_cfg)
def make_folder_tech_doc(
    codebase_name: str, node: LiteNode, child_nodes_to_docs: dict[LiteNode, dict]
) -> dict[str, any]:
    from inspection.folders import comprehend_folder_top_down
    from utils.models import ChatOpenAI

    llm = ChatOpenAI(model="gpt-4o", temperature=0, request_timeout=120)

    print(f"Processing folder tech docs for ({node})")
    folder_docs = comprehend_folder_top_down(
        llm=llm,
        codebase_name=codebase_name,
        node=node,
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        max_workers=1,
        child_nodes_to_docs=child_nodes_to_docs,
        compression_loop_max_itr=COMPRESSION_LOOP_MAX_ITR,
    )
    print(f"Folder tech docs created for ({node})")
    return folder_docs


@app.function(concurrency_limit=3, **function_cfg)
def make_toplevel_tech_docs(
    codebase_name: str, nodes_to_docs: dict[LiteNode, dict]
) -> dict[str, any]:
    from inspection.toplevel import comprehend_codebase_top_down
    from utils.models import ChatOpenAI

    llm = ChatOpenAI(model="gpt-4o", temperature=0, request_timeout=120)

    print(f"Processing top-level docs for `{codebase_name}`")
    top_level_docs = comprehend_codebase_top_down(
        llm=llm,
        docs=nodes_to_docs,
        codebase_name=codebase_name,
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        max_workers=1,
        include_exploratory_generation=False,
        compression_loop_max_itr=COMPRESSION_LOOP_MAX_ITR,
    )
    print(f"Processed top-level docs for `{codebase_name}`")
    return top_level_docs


CHUNK_SIZE = 280_000
CHUNK_OVERLAP = 10_000
COMPRESSION_LOOP_MAX_ITR = 10
MAX_NUM_CHUNKS_FILE = 3
