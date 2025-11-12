from datetime import timedelta
from pathlib import Path

from hatchet_client import hatchet
from hatchet_sdk import Context
from inspector.src.modal_funcs import (
    make_folder_tech_doc,
    make_symbol_docs,
    make_tech_doc,
    make_toplevel_tech_docs,
)
from pydantic import BaseModel
from shared.inspector.utils.dag import LiteNode, NodeKind


class TechDocInput(BaseModel):
    node: LiteNode
    codebase_name: str
    source_code: str
    version_id: str


class FolderDocInput(BaseModel):
    node: LiteNode
    codebase_name: str
    child_nodes_to_docs: list[tuple[LiteNode, dict]]
    previous_content: dict[str, str] | None


class SymbolDocInput(BaseModel):
    node: LiteNode
    source_code: str
    file_description_paragraph: str
    symbol_count_limit: int | None


class TopLevelDocInput(BaseModel):
    codebase_name: str
    nodes_to_docs: list[tuple[LiteNode, dict]]


@hatchet.task(name="tech-doc-workflow", execution_timeout=timedelta(minutes=60))
def tech_doc_task(input: TechDocInput, ctx: Context) -> dict[str, str]:
    print("starting tech doc task")
    # Call the function to generate tech docs
    node_kind = NodeKind(input.node["kind"])
    node_root_rel_path = Path(input.node["root_rel_path"])
    node_status = input.node["status"]
    node = LiteNode(
        kind=node_kind,
        root_rel_path=node_root_rel_path,
        status=node_status,
    )
    tech_docs = make_tech_doc(
        node,
        input.codebase_name,
        input.source_code,
        input.version_id,
    )
    print("executed tech doc task")
    return tech_docs


@hatchet.task(name="folder-doc-workflow", execution_timeout=timedelta(minutes=60))
def folder_doc_task(input: FolderDocInput, ctx: Context) -> dict[str, str]:
    print("starting folder doc task")
    # Call the function to generate folder docs

    node_kind = NodeKind(input.node["kind"])
    node_root_rel_path = Path(input.node["root_rel_path"])
    node_status = input.node["status"]
    node = LiteNode(
        kind=node_kind,
        root_rel_path=node_root_rel_path,
        status=node_status,
    )
    print(node.root_rel_path.name)
    child_nodes_to_docs = {}
    for child_node, doc in input.child_nodes_to_docs:
        child_node_kind = NodeKind(child_node["kind"])
        child_node_root_rel_path = Path(child_node["root_rel_path"])
        child_node_status = child_node["status"]
        child_node = LiteNode(
            kind=child_node_kind,
            root_rel_path=child_node_root_rel_path,
            status=child_node_status,
        )
        child_nodes_to_docs[child_node] = doc
    folder_docs = make_folder_tech_doc(
        input.codebase_name,
        node,
        child_nodes_to_docs,
        input.previous_content,
    )
    print("executed folder doc task")
    return folder_docs


@hatchet.task(name="symbol-doc-workflow", execution_timeout=timedelta(minutes=60))
def symbol_doc_task(input: SymbolDocInput, ctx: Context) -> list[dict[str, any]]:
    print("starting symbol doc task")
    # Call the function to generate symbol docs
    node_kind = NodeKind(input.node["kind"])
    node_root_rel_path = Path(input.node["root_rel_path"])
    node_status = input.node["status"]
    node = LiteNode(
        kind=node_kind,
        root_rel_path=node_root_rel_path,
        status=node_status,
    )
    symbol_docs = make_symbol_docs(
        node,
        input.source_code,
        input.file_description_paragraph,
        input.symbol_count_limit,
    )
    print("executed symbol doc task")
    return symbol_docs


@hatchet.task(name="toplevel-doc-workflow", execution_timeout=timedelta(minutes=60))
def toplevel_doc_task(input: TopLevelDocInput, ctx: Context) -> dict[str, any]:
    print("starting toplevel doc task")
    # Call the function to generate toplevel docs
    nodes_to_docs = {}
    for node, doc in input.nodes_to_docs:
        node_kind = NodeKind(node["kind"])
        node_root_rel_path = Path(node["root_rel_path"])
        node_status = node["status"]
        node = LiteNode(
            kind=node_kind,
            root_rel_path=node_root_rel_path,
            status=node_status,
        )
        nodes_to_docs[node] = doc
    toplevel_docs = make_toplevel_tech_docs(
        input.codebase_name,
        nodes_to_docs,
    )
    print("executed toplevel doc task")
    return toplevel_docs
