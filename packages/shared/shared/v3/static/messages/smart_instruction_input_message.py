from shared.v3.messages.llm_message import LlmMessage, MessageKind
from shared.v3.messages.llm_message_kind import MessageKind
from shared.v3.static.messages.global_message_constants import (
    DOCUMENT_CONTENT_AFTER_CURSOR_XML_BEGIN,
    DOCUMENT_CONTENT_AFTER_CURSOR_XML_END,
    DOCUMENT_CONTENT_BEFORE_CURSOR_XML_BEGIN,
    DOCUMENT_CONTENT_BEFORE_CURSOR_XML_END,
    PROMPT_XML_BEGIN,
    PROMPT_XML_END,
    USER_CURSOR_XML_BEGIN,
    USER_CURSOR_XML_END,
    USER_SELECTED_TEXT_XML_BEGIN,
    USER_SELECTED_TEXT_XML_END,
)


class SmartInstructionInputMessage(LlmMessage):
    message_kind: MessageKind = MessageKind.USER

    @classmethod
    def from_context(
        cls,
        prompt: str,
        before: str,
        after: str,
        selected_text: str | None = None,
    ) -> "SmartInstructionInputMessage":
        content = (
            f"The user has entered the following prompt:"
            f"{PROMPT_XML_BEGIN}{prompt}{PROMPT_XML_END}"
            f"{f'{USER_SELECTED_TEXT_XML_BEGIN}{selected_text}{USER_SELECTED_TEXT_XML_END}' if selected_text else ''}"
            f"{f'{DOCUMENT_CONTENT_BEFORE_CURSOR_XML_BEGIN}{before}{DOCUMENT_CONTENT_BEFORE_CURSOR_XML_END}' if before.strip() else ''}"
            f"{f'{USER_CURSOR_XML_BEGIN}{selected_text}{USER_CURSOR_XML_END}' if selected_text else '<USER_CURSOR>'}"
            f"{f'{DOCUMENT_CONTENT_AFTER_CURSOR_XML_BEGIN}{after}{DOCUMENT_CONTENT_AFTER_CURSOR_XML_END}' if after.strip() else ''}"
        )
        return cls(content=content.strip())
