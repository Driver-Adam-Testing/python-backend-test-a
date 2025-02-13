from shared.v3.messages.llm_message import LlmMessage
from shared.v3.messages.llm_message_kind import MessageKind

MESSAGE_MULTI_ITERATION_SYSTEM = LlmMessage(
    message_kind=MessageKind.SYSTEM,
    content=(
        "You are operating in a multi-iteration, multi-step mode. "
        "In this mode, tasks are broken down into several iterations and steps to ensure thorough analysis "
        "and comprehensive responses. "
        "Within each iteration, you may execute tools, gather additional context, and refine your answers based on "
        "previous outputs. "
        "This process continues until the task is completed to the highest standard."
    ),
)

MESSAGE_FIRST_ITERATION = LlmMessage(
    message_kind=MessageKind.ITERATION,
    content=(
        "Execute Tools.\n"
        "This is the first iteration, and tools must be executed to retrieve initial context.\n"
        "You have {remaining_iterations} more opportunities to execute tools."
    ),
)

MESSAGE_MIDDLE_ITERATION = LlmMessage(
    message_kind=MessageKind.ITERATION,
    content=(
        "Return a Response ONLY if you have above 90 percent confidence that you have been as specific "
        "and comprehensive as possible in your response.\n"
        "If there is additional context required to become absolutely confident, Execute Tools.\n"
        "If you haven't executed every kind of tool, Execute Tools.\n"
        "If there may be additional relevant context, Execute Tools.\n\n"
        "You have {remaining_iterations} more opportunities to execute tools."
    ),
)

MESSAGE_FINAL_ITERATION = LlmMessage(
    message_kind=MessageKind.ITERATION,
    content=(
        "Return A Response. This is the final iteration, and a response must be returned."
    ),
)


def get_iteration_message(iteration: int, total_iterations: int) -> LlmMessage:
    remaining_iterations = total_iterations - iteration

    if iteration == 1:
        return LlmMessage(
            message_kind=MessageKind.USER,
            content=(
                "Execute Tools.\n"
                "This is the first iteration, and tools must be executed to retrieve initial context.\n"
                f"You have {remaining_iterations} more opportunities to execute tools."
            ),
        )
    elif iteration < total_iterations:
        return LlmMessage(
            message_kind=MessageKind.USER,
            content=(
                "Return a Response ONLY if you have above 90 percent confidence that you have been as specific "
                "and comprehensive as possible in your response.\n"
                "If there is additional context required to become absolutely confident, Execute Tools.\n"
                "If you haven't executed every kind of tool, Execute Tools.\n"
                "If there may be additional relevant context, Execute Tools.\n\n"
                f"You have {remaining_iterations} more opportunities to execute tools."
            ),
        )
    else:
        return LlmMessage(
            message_kind=MessageKind.USER,
            content=(
                "Return A Response. This is the final iteration, and a response must be returned."
            ),
        )
