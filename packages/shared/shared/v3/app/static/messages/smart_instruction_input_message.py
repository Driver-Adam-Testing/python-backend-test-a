from shared.v3.globals.glossary import (
    CURSOR,
    DOCUMENT_CONTENT,
    DOCUMENT_CONTENT_AFTER_CURSOR,
    DOCUMENT_CONTENT_BEFORE_CURSOR,
    USER_PROMPT,
)
from shared.v3.interfaces.llm_message import LlmMessage, MessageKind


class SmartInstructionInputMessage(LlmMessage):
    message_kind: MessageKind = MessageKind.USER

    @classmethod
    def from_context(
        cls,
        prompt: str,
        page_content_before_cursor: str | None = None,
        page_content_after_cursor: str | None = None,
    ) -> "SmartInstructionInputMessage":
        document_content = DOCUMENT_CONTENT.wrap(
            DOCUMENT_CONTENT_BEFORE_CURSOR.wrap(page_content_before_cursor)
            + CURSOR.wrap("", annotate_empty=True)
            + DOCUMENT_CONTENT_AFTER_CURSOR.wrap(page_content_after_cursor)
        )
        content = (
            f"The user has entered the following request:\n"
            f"{USER_PROMPT.wrap(prompt)}\n"
            f"{document_content}"
        )
        return cls(content=content.strip())
