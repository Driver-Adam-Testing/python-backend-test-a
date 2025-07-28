from shared.v3.globals.constants import IMPORTANT
from shared.v3.interfaces.llm_message import LlmMessage
from shared.v3.interfaces.llm_message_kind import MessageKind


class MultiShotIterationContextMessage(LlmMessage):
    message_kind: MessageKind = MessageKind.ITERATION
    content: str = (
        "You are operating in multi-iteration mode. "
        "You must iterate until the task is resolved to the highest quality. "
        "You will be given a task, and be notified of the iterations that remain. Each iteration, you can execute tools, or return the final assistant response. "
        f"{IMPORTANT} The final assistant response is NEVER a tool call or a description of a tool call. It is always a markdown response. "
        "If you do not have enough information to return a final assistant response, display a message about the information you may need, and encourage the user to refine their request and try again."
        "If the user greets you, or makes a small talk, respond with a greeting and encouragement to ask technical questions. In the case of small talk, no need to use tools. \n"
    )


class IterationMessage(LlmMessage):
    message_kind: MessageKind = MessageKind.ITERATION

    @classmethod
    def from_context(cls, iteration: int, total_iterations: int) -> "IterationMessage":
        remaining = total_iterations - iteration

        if iteration == 1:
            content = (
                "This is the first iteration. You must execute tools to retrieve the user's uploaded source code, documentation, and pdfs, unless the user's request is a greeting, small talk, or questions about the Driver chatbot. \n"
                "You may forgo tool execution and instead answer the user's request, but only if the user request is irrelevant with to the uploaded source code, documentation, and pdfs. \n"
                f"{remaining} additional tool executions remain."
            )
        elif iteration < total_iterations:
            content = (
                "Return a response ONLY if you have 100% Confidence that you have complete context about a user's uploaded materials. \n"
                "If additional context is needed, if not all tool types have been executed, or if more relevant context may exist, execute tools. \n"
                f"{remaining} available tool executions remain."
            )
        else:
            content = "This is the final iteration. Return a response."

        return cls(content=content)
