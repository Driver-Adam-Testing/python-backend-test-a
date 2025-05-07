from shared.v3.globals.glossary import (
    CURSOR,
    CURSOR_SELECTION,
    DOCUMENT_CONTENT_AFTER_CURSOR,
    DOCUMENT_CONTENT_BEFORE_CURSOR,
    USER_PROMPT,
    WORKING_DOCUMENT_CONTENT,
)
from shared.v3.interfaces.llm_message import LlmMessage, MessageKind


class InlineEditSystemMessage(LlmMessage):
    message_kind: MessageKind = MessageKind.SYSTEM
    content: str = (
        "You are a skilled technical writer who excels at refining text in response to a user prompt. "
        "The user has highlighted or positioned the cursor on a specific segment of the document—this is the text they wish to change. "
        "Your revised text will replace only the selected content. "
        "In an inline edit request, "
        f"{USER_PROMPT.xml_begin} marks the user prompt, "
        f"{CURSOR_SELECTION.xml_begin} marks the selected text, and "
        f"{DOCUMENT_CONTENT_BEFORE_CURSOR.xml_begin} and {DOCUMENT_CONTENT_AFTER_CURSOR.xml_begin} respectively mark the remainder of the document before and after the cursor. "
        f"The user prompt, shown as {USER_PROMPT.xml_begin}, will detail the changes required for the selected text. "
        "Your final answer must replace only the selected portion of the text, with no additional content. "
        "The system managing the page content will handle inserting your response into the document."
    )


class InlineEditToolUseMessage(LlmMessage):
    message_kind: MessageKind = MessageKind.SYSTEM
    content: str = "If the user prompt contains questions about information that is not explicitly in the document before or after the selected text, you must use tools to get the context from the source code or documentation."


class InlineEditUserMessage(LlmMessage):
    message_kind: MessageKind = MessageKind.USER

    @classmethod
    def from_context(
        cls,
        user_prompt: str,
        page_content_before_cursor: str,
        selected_text: str,
        page_content_after_cursor: str,
    ) -> "InlineEditUserMessage":
        return cls(
            content=(
                f""
                f"{USER_PROMPT.wrap(user_prompt)}"
                f"{WORKING_DOCUMENT_CONTENT.wrap(
                    DOCUMENT_CONTENT_BEFORE_CURSOR.wrap(page_content_before_cursor)+
                    CURSOR.wrap(CURSOR_SELECTION.wrap(selected_text))+
                    DOCUMENT_CONTENT_AFTER_CURSOR.wrap(page_content_after_cursor))}"
            )
        )
