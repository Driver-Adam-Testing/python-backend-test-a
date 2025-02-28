from shared.v3.app.static.messages.constants import (
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
from shared.v3.interfaces.llm_message import LlmMessage, MessageKind


class SmartInstructionInputMessage(LlmMessage):
    message_kind: MessageKind = MessageKind.USER

    @classmethod
    def from_context(
        cls,
        prompt: str,
        page_content_before_cursor: str | None = None,
        page_content_after_cursor: str | None = None,
        selected_text: str | None = None,
    ) -> "SmartInstructionInputMessage":
        content = (
            f"The user has entered the following request:"
            f"{PROMPT_XML_BEGIN}{prompt}{PROMPT_XML_END}"
            f"{f'{USER_SELECTED_TEXT_XML_BEGIN}{selected_text}{USER_SELECTED_TEXT_XML_END}' if selected_text else ''}"
            f"{f'{DOCUMENT_CONTENT_BEFORE_CURSOR_XML_BEGIN}{page_content_before_cursor}{DOCUMENT_CONTENT_BEFORE_CURSOR_XML_END}' if page_content_before_cursor and page_content_before_cursor.strip() else ''}"
            f"{f'{USER_CURSOR_XML_BEGIN}{selected_text}{USER_CURSOR_XML_END}' if selected_text else '<USER_CURSOR>'}"
            f"{f'{DOCUMENT_CONTENT_AFTER_CURSOR_XML_BEGIN}{page_content_after_cursor}{DOCUMENT_CONTENT_AFTER_CURSOR_XML_END}' if page_content_after_cursor and page_content_after_cursor.strip() else ''}"
        )
        return cls(content=content.strip())
