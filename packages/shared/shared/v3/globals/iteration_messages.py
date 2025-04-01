from shared.v3.interfaces.llm_message import LlmMessage
from shared.v3.interfaces.llm_message_kind import MessageKind


class MultiShotIterationContextMessage(LlmMessage):
    message_kind: MessageKind = MessageKind.ITERATION
    content: str = (
        "You are operating to fulfil a single request in multi-iteration mode: you must respond to a single iteration request, so that the final response is exhaustive and optimized. "
        "In each iteration, you must execute tools, retrieve additional context, and refine outputs based on prior results. "
        "You must iterate until the task is resolved to the highest quality."
    )


class IterationMessage(LlmMessage):
    message_kind: MessageKind = MessageKind.ITERATION

    @classmethod
    def from_context(cls, iteration: int, total_iterations: int) -> "IterationMessage":
        remaining = total_iterations - iteration

        if iteration == 1:
            content = (
                "This is the first iteration. You must execute tools to retrieve the user's uploaded source code, documentation, and pdfs. "
                "You may forgo tool execution and instead answer the user's request, but only if the user request is irrelevant with to the uploaded source code, documentation, and pdfs. "
                f"{remaining} additional tool executions remain."
            )
        elif iteration < total_iterations:
            content = (
                "Return a response ONLY if you have 100% Confidence that you have complete context about a user's uploaded materials."
                "If additional context is needed, if not all tool types have been executed, or if more relevant context may exist, execute tools. "
                f"{remaining} available tool executions remain."
            )
        else:
            content = "This is the final iteration. Return a response."

        return cls(content=content)
