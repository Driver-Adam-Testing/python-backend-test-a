from shared.v3.app.static.messages.constants import (
    DOCUMENT_CONTENT_AFTER_CURSOR_XML_BEGIN,
    DOCUMENT_CONTENT_AFTER_CURSOR_XML_END,
    DOCUMENT_CONTENT_BEFORE_CURSOR_XML_BEGIN,
    DOCUMENT_CONTENT_BEFORE_CURSOR_XML_END,
    IMPORTANT,
    PROMPT_XML_BEGIN,
    PROMPT_XML_END,
    USER_SELECTED_TEXT_XML_BEGIN,
    USER_SELECTED_TEXT_XML_END,
)
from shared.v3.interfaces.llm_message import LlmMessage, MessageKind


class AbbreviatePageContentSystemMessage(LlmMessage):
    # TODO: Shorten this message.
    content: str = (
        "You are an expert in converting document sections into relevant, information dense, terse context for agentic systems. "
        "A user selects part of a document (which might be very large or very short) and provides unformatted surrounding text—from both before and after the selection. "
        "These surrounding snippets can include prose, code snippets, section headers, technical notes, or anything else contained in the document. \n"
        "If the document part does not contain any relevant information, return an empty string. \n"
        f"{IMPORTANT} If the text about the codebase is not in the document, it must be searched for by the agent in the future. Do not assume information that is not in the document.\n"
        f"{IMPORTANT} Do not return likely interpretations of the information in the document. Only return the actual information in the document.\n"
        "Your job is to preprocess and structure this part of the document so that a downstream LLM can effectively use it. Specifically, you should:\n"
        "- Supply relevant background details and existing relevantinformation from the document so that the LLM does not need to seek external sources unnecessarily.\n"
        "- Clarify the precise location and scope of the selected text within the document, highlighting its relation to neighboring sections or code snippets.\n"
        "- Identify what document parts are already present, helping the LLM avoid duplicating or repeating information when composing or revising text.\n"
        "- Summarize the document part in a way that is easy to understand and use.\n"
        "By fulfilling these objectives, you ensure the downstream LLM has the context it needs to produce clear, accurate, and non-redundant technical documentation or long-form explanations about the codebase or subject matter."
    )
    message_kind: MessageKind = MessageKind.SYSTEM


class AbbreviatePageContentUserMessage(LlmMessage):
    message_kind: MessageKind = MessageKind.USER

    @classmethod
    def from_context(
        cls,
        prompt: str,
        page_content: str,
        before: bool,
        selected_text: str | None = None,
    ) -> "AbbreviatePageContentUserMessage":
        content = (
            "Given the following user prompt, some page content, and cursor position, please provide a concise, information-dense summary of the relevant parts of the document."
            "If the page content is not relevant to the user prompt, return an empty string."
            f"{PROMPT_XML_BEGIN}{prompt}{PROMPT_XML_END}\n"
            f"{f'{DOCUMENT_CONTENT_BEFORE_CURSOR_XML_BEGIN}{page_content}{DOCUMENT_CONTENT_BEFORE_CURSOR_XML_END}\n' if before else ''}"
            f"{f'{USER_SELECTED_TEXT_XML_BEGIN}{selected_text}{USER_SELECTED_TEXT_XML_END}\n' if selected_text and selected_text.strip() else ''}"
            f"{f'{DOCUMENT_CONTENT_AFTER_CURSOR_XML_BEGIN}{page_content}{DOCUMENT_CONTENT_AFTER_CURSOR_XML_END}\n' if not before else ''}"
        ).strip()
        return cls(content=content)
