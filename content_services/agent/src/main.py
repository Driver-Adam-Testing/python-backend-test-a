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


# # TODO: get the version of this docker container
# mermaid_cli_image = modal.Image.from_registry("minlag/mermaid-cli", add_python="3.11")


# @app.function(timeout=3600, image=mermaid_cli_image, keep_warm=1)
# def verify_mermaid_render(input: str) -> any:
#     import tempfile
#     import subprocess

#     with tempfile.NamedTemporaryFile(mode="w", suffix=".mmd", delete=False) as tmp_file:
#         tmp_file.write(input)
#         tmp_file.flush()
#         mermaid_filepath = tmp_file.name

#     # We don't actually need the output file, but we must give mmdc an output path.
#     with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as output_file:
#         output_path = output_file.name

#     try:
#         # Try rendering. If mmdc cannot parse the file, it will raise CalledProcessError.
#         subprocess.check_output(
#             [
#                 "mmdc",
#                 "-i",
#                 mermaid_filepath,
#                 "-o",
#                 output_path,
#             ],
#             stderr=subprocess.STDOUT,
#         )
#         # If successful, the code is valid
#         return True, None

#     except subprocess.CalledProcessError as e:
#         # In case the command fails, capture the output for debugging
#         error_message = e.output.decode("utf-8", errors="ignore")
#         print("Mermaid CLI error:", error_message)
#         return False, error_message

#     finally:
#         # Clean up: remove temporary files
#         if os.path.exists(mermaid_filepath):
#             os.remove(mermaid_filepath)
#         if os.path.exists(output_path):
#             os.remove(output_path)


# @app.local_entrypoint()
# def main():
#     print(
#         verify_mermaid_render.remote("graph TD UNRENDERABLE (MERMAID) SYNTAX A --> B\n")
#     )
