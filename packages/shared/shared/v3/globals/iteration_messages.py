from shared.v3.interfaces.llm_message import LlmMessage
from shared.v3.interfaces.llm_message_kind import MessageKind


class MultiShotSystemMessage(LlmMessage):
    message_kind: MessageKind = MessageKind.SYSTEM
    content: str = (
        "Operate in multi-iteration, multi-step mode: decompose tasks into iterative phases for exhaustive analysis and optimized responses. "
        "In each iteration, execute tools, retrieve additional context, and refine outputs based on prior results. "
        "Iterate until the task is resolved to the highest quality."
    )


class IterationMessage(LlmMessage):
    message_kind: MessageKind = MessageKind.ITERATION

    @classmethod
    def from_context(cls, iteration: int, total_iterations: int) -> "IterationMessage":
        remaining = total_iterations - iteration

        if iteration == 1:
            content = (
                "Execute Tools: First iteration mandates tool execution to acquire initial context. "
                f"{remaining} additional tool executions remain."
            )
        elif iteration < total_iterations:
            content = (
                "Return a response ONLY if confidence exceeds 90% in its specificity and completeness. "
                "If additional context is needed, if not all tool types have been executed, or if more relevant context may exist, execute tools. "
                f"{remaining} tool executions remain."
            )
        else:
            content = "Return a response: Final iteration requires output."

        return cls(content=content)
