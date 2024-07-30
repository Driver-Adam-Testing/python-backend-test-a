from modal import Function
from modal.functions import FunctionCall
from app.core.config import settings

from app.instructions.types import Instruction


def execute_instruction(workspace_id: str, codebase_id: str, prompt: str) -> str:
    if prompt is None:
        raise Exception("Prompt is required")

    if workspace_id is None:
        raise Exception("Workspace ID is required")

    # prompt = body.prompt
    single_shot_edit = Function.lookup(
        "comprehender",
        "single_shot_edit",
        environment_name=settings.MODAL_ENVIRONMENT)

    call_response = single_shot_edit.spawn(
        str(workspace_id), str(codebase_id), prompt, None
    )

    if call_response is None:
        raise Exception("Failed to spawn function call")

    print(call_response)
    return str(call_response.object_id)


def get_execution_result(call_id: str) -> Instruction:
    if call_id is None:
        raise Exception("Call ID is required")

    instruction_result = Instruction(call_id=call_id)

    function_call = FunctionCall.from_id(call_id)
    try:
        result = function_call.get(timeout=0)
        instruction_result.status = "completed"
        instruction_result.response = result.get("content")
    except TimeoutError:
        instruction_result.status = "running"
        instruction_result.response = ""
    except Exception:
        instruction_result.status = "expired"
        instruction_result.error = "Output expired"

    print(instruction_result)

    return instruction_result


def get_batch_execution_results(call_ids: list[str]) -> list[Instruction]:
    if call_ids is None:
        raise Exception("Call IDs are required")

    results: list[Instruction] = []

    for call_id in call_ids:
        instruction_result = get_execution_result(call_id)

        results.append(instruction_result)

    return results
