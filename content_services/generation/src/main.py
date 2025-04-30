from collections.abc import AsyncGenerator

import modal
from shared.v3.interfaces.llm_stream_response import LlmStreamResponse

app = modal.App(name="generation")

image = modal.Image.debian_slim(python_version="3.12").pip_install("fastapi[standard]")
image = (
    modal.Image.debian_slim(python_version="3.12")
    .copy_local_dir("../../driver_db/", remote_path="/driver_db")
    .copy_local_dir(local_path="../../packages/shared", remote_path="/packages/shared")
    .poetry_install_from_file("pyproject.toml")
)

secrets = [
    modal.Secret.from_name("open-ai"),
    modal.Secret.from_name("db"),
    modal.Secret.from_name("aws-inspector-s3"),
]


@app.function(image=image, secrets=secrets)
async def inline_edit_stream(input: dict) -> AsyncGenerator[LlmStreamResponse, None]:
    from shared.v3.app.pipelines.inline_edit import (
        InlineEditPipelineRequest,
    )

    parsed_input = InlineEditPipelineRequest.from_dict(input)
    async for chunk in parsed_input.stream():
        yield chunk


@app.function(image=image, secrets=secrets)
async def inline_edit_run(input: dict) -> AsyncGenerator[LlmStreamResponse, None]:
    from shared.v3.app.pipelines.inline_edit import InlineEditPipelineRequest

    parsed_input = InlineEditPipelineRequest.from_dict(input)
    return parsed_input.run()


@app.function(image=image, secrets=secrets)
async def smart_instruction_stream(
    input: dict,
) -> AsyncGenerator[LlmStreamResponse, None]:
    from shared.v3.app.pipelines.smart_instruction import (
        SmartInstructionPipelineRequest,
    )

    parsed_input = SmartInstructionPipelineRequest.from_dict(input)
    async for chunk in parsed_input.stream():
        yield chunk


@app.function(image=image, secrets=secrets)
async def smart_instruction_run(input: dict) -> AsyncGenerator[LlmStreamResponse, None]:
    from shared.v3.app.pipelines.smart_instruction import (
        SmartInstructionPipelineRequest,
    )

    parsed_input = SmartInstructionPipelineRequest.from_dict(input)
    return parsed_input.run()
