"""
This file exposes the modal (https://www.modal.com) interface for the agent package.
"""

import os

import modal

app = modal.App("agent")


image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("nodejs", "npm")
    .add_local_dir("../../driver_db/", remote_path="/driver_db", copy=True)
    .add_local_dir(
        local_path="../../packages/shared", remote_path="/packages/shared", copy=True
    )
    .poetry_install_from_file("pyproject.toml")
)

agent_model_config = {
    "image": image,
    "secrets": [
        modal.Secret.from_name("open-ai"),
        modal.Secret.from_name("db"),
        modal.Secret.from_name("aws-inspector-s3"),
    ],
    "max_containers": 36,
}


agent_model_config["proxy"] = (
    modal.Proxy.from_name("my-proxy")
    if os.environ["MODAL_ENVIRONMENT"] in ["dev", "staging"]
    else modal.Proxy.from_name("my-proxy", environment_name="prod")
)


@app.function(timeout=3600, **agent_model_config, min_containers=0)
def run(input: dict) -> any:
    from shared.interfaces.agents.pipeline_configuration import BlockKind, PipelineInput
    from shared.pipelines.agents.execute import execute_sequence
    from shared.pipelines.block_kind_pipelines.code import execute_code_block_agent
    from shared.pipelines.block_kind_pipelines.diagram import (
        execute_diagram_block_agent,
    )
    from shared.pipelines.block_kind_pipelines.list import execute_list_block_agent
    from shared.pipelines.block_kind_pipelines.table import execute_table_block_agent

    parsed_input = input if isinstance(input, PipelineInput) else PipelineInput(**input)
    # Use the response_format type directly for execution
    match parsed_input.block_kind:
        case BlockKind.LIST:
            return execute_list_block_agent(input).model_dump()
        case BlockKind.TABLE:
            return execute_table_block_agent(input).model_dump()
        case BlockKind.DIAGRAM:
            return execute_diagram_block_agent(input).model_dump()
        case BlockKind.CODE:
            parsed_input.prompt = f"{parsed_input.prompt}\n\nBe sure to include the language identifiers in the code blocks."
            return execute_code_block_agent(input).model_dump()
        case BlockKind.TEXT:
            parsed_input.prompt = f"{parsed_input.prompt}\n\nContent returned should be a single paragraph of text."
        case BlockKind.ANY:
            parsed_input.response_format = None

    return execute_sequence(parsed_input).model_dump()
