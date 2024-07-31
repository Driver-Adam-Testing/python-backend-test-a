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

    return str(call_response.object_id)


def get_execution_result(call_id: str) -> Instruction:
    response = None
    error = ""
    function_call = FunctionCall.from_id(call_id)
    try:
        result = function_call.get(timeout=0)
        status = "completed"
        response = result["content"]
    except TimeoutError:
        status = "running"
    except Exception as e:
        # TODO: Log the exception
        # logger.warning(e)
        # This is swallowing all errors because the way modal responds to errors is not consistent
        status = "expired"
        error = "Output expired"

    return Instruction(
        call_id=call_id,
        status=status,
        response=response,
        error=error,
        references=[]
    )


def get_batch_execution_results(call_ids: list[str]) -> list[Instruction]:
    return [get_execution_result(call_id) for call_id in call_ids]
