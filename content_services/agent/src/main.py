"""
This file exposes the modal (https://www.modal.com) interface for the agent package.
"""

import os

import modal

app = modal.App("agent")


image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("nodejs", "npm")
    .run_commands("npm install -g @mermaid-js/mermaid-cli")
    .copy_local_dir("../../driver_db/", remote_path="/driver_db")
    .copy_local_dir(local_path="../../packages/shared", remote_path="/packages/shared")
    .poetry_install_from_file("pyproject.toml")
)

agent_model_config = {
    "image": image,
    "mounts": [
        modal.Mount.from_local_dir(
            local_path="../../driver_db/certs",
            remote_path="/root/data/",
        ),
    ],
    "secrets": [
        modal.Secret.from_name("open-ai"),
        modal.Secret.from_name("db"),
        modal.Secret.from_name("aws-inspector-s3"),
    ],
    "concurrency_limit": 36,
}

if os.environ["MODAL_ENVIRONMENT"] != "staging":
    agent_model_config["proxy"] = modal.Proxy.from_name("pg-proxy")


@app.function(timeout=3600, **agent_model_config, keep_warm=10)
def run(input: dict) -> any:
    from shared.interfaces.agents.pipeline_configuration import PipelineInput
    from shared.pipelines.agents.execute import execute_sequence
    from shared.pipelines.block_kind_pipelines.code import execute_code_block_agent
    from shared.pipelines.block_kind_pipelines.diagram import (
        execute_diagram_block_agent,
    )
    from shared.pipelines.block_kind_pipelines.list import execute_list_block_agent
    from shared.pipelines.block_kind_pipelines.table import execute_table_block_agent

    # from shared.prompts.block_kind.block_kind_any import BlockKindCopyEditorAny
    from shared.prompts.block_kind.block_kind_code import BlockKindCopyEditorCodeBlock
    from shared.prompts.block_kind.block_kind_diagram import BlockKindCopyEditorDiagram
    from shared.prompts.block_kind.block_kind_list import BlockKindCopyEditorList
    from shared.prompts.block_kind.block_kind_table import BlockKindCopyEditorTable
    # from shared.prompts.block_kind.block_kind_text import BlockKindCopyEditorText

    if isinstance(input, dict):
        input = PipelineInput(**input)
        print(input.model_dump())
    # Use the response_format type directly for execution
    if isinstance(input.response_format, BlockKindCopyEditorList):
        return execute_list_block_agent(input).model_dump()
    elif isinstance(input.response_format, BlockKindCopyEditorTable):
        return execute_table_block_agent(input).model_dump()
    elif isinstance(input.response_format, BlockKindCopyEditorDiagram):
        return execute_diagram_block_agent(input).model_dump()
    elif isinstance(input.response_format, BlockKindCopyEditorCodeBlock):
        return execute_code_block_agent(input).model_dump()
    # elif isinstance(input.response_format, BlockKindCopyEditorText):
    #     return execute_text_block_agent(input).model_dump()
    # elif isinstance(input.response_format, BlockKindCopyEditorAny):
    #     return execute_any_block_agent(input).model_dump()
    return execute_sequence(input).model_dump()
