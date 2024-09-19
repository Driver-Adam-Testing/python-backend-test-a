"""
This file exposes the modal (https://www.modal.com) interface for the comprehender package.
"""

import modal

app = modal.App("agent")


# Note, all these schenanigans are required because `poetry_install_from_file` doesn't install our comprehender-database
# package, which is a *local* package in pyproject.toml of comprehender.
image = (
    modal.Image.debian_slim(python_version="3.12")
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
    ],
    "proxy": modal.Proxy.from_name("pg-proxy"),
    "concurrency_limit": 5,
    "region": "us-east",
}


@app.function(timeout=3600, **agent_model_config, keep_warm=1)
def run(input: dict):
    from shared.interfaces.agents.pipeline_configuration import PipelineInput
    from shared.pipelines.agents.execute import execute_sequence

    if isinstance(input, dict):
        input = PipelineInput(**input)

    return execute_sequence(input).model_dump()
