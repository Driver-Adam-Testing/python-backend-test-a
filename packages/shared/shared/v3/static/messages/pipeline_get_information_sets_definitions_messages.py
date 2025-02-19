from shared.v3.interfaces.llm_message import LlmMessage, MessageKind
from shared.v3.static.messages.global_message_constants import (
    DOCUMENT_CONTENT_AFTER_CURSOR_XML_BEGIN,
    DOCUMENT_CONTENT_AFTER_CURSOR_XML_END,
    DOCUMENT_CONTENT_BEFORE_CURSOR_XML_BEGIN,
    DOCUMENT_CONTENT_BEFORE_CURSOR_XML_END,
    PROMPT_XML_BEGIN,
    PROMPT_XML_END,
    USER_SELECTED_TEXT_XML_BEGIN,
    USER_SELECTED_TEXT_XML_END,
)


class InformationSetsSystemMessage(LlmMessage):
    content: str = (
        "You are an expert in defining information sets for multi-step request fullfilment systems."
        "In order to fulfill a user request, it is important to first define what information is required to fulfill the request."
        "The request will not be fulfilled until all Information Sets are retrieved."
        "Information Sets are collections of information that are relevant and necessary to fultill a user request."
        "Information Sets can be provided by the user or can be retrieved from external sources."
    )
    message_kind: MessageKind = MessageKind.SYSTEM


class GetInformationSetsUserMessage(LlmMessage):
    message_kind: MessageKind = MessageKind.USER

    @classmethod
    def from_context(
        cls,
        prompt: str,
        page_content_before_cursor: str | None = None,
        page_content_after_cursor: str | None = None,
        selected_text: str | None = None,
    ) -> "GetInformationSetsUserMessage":
        content = (
            "Given the following user prompt, return a list of Information Sets that are relevant to the user prompt."
            f"{PROMPT_XML_BEGIN}{prompt}{PROMPT_XML_END}\n"
            f"{f'{USER_SELECTED_TEXT_XML_BEGIN}{selected_text}{USER_SELECTED_TEXT_XML_END}\n' if selected_text and selected_text.strip() else ''}"
            f"{f'{DOCUMENT_CONTENT_BEFORE_CURSOR_XML_BEGIN}{page_content_before_cursor}{DOCUMENT_CONTENT_BEFORE_CURSOR_XML_END}\n' if page_content_before_cursor and page_content_before_cursor.strip() else ''}"
            f"{f'{USER_SELECTED_TEXT_XML_BEGIN}{selected_text}{USER_SELECTED_TEXT_XML_END}\n' if selected_text and selected_text.strip() else ''}"
            f"{f'{DOCUMENT_CONTENT_AFTER_CURSOR_XML_BEGIN}{page_content_after_cursor}{DOCUMENT_CONTENT_AFTER_CURSOR_XML_END}\n' if page_content_after_cursor and page_content_after_cursor.strip() else ''}"
        ).strip()
        return cls(content=content)


class GetInformationSetsParametersSystemMessage(LlmMessage):
    content: str = (
        "InformationSetParameters define the mechanisms by which you will retrieve information for an InformationSet.\n"
        "InformationSetParameters include the query strings, comparison affirm, comparison negate, bounding, query type, element analysis, and exhaustive.\n"
        "The system will search in either EXACT_MATCH_KEYWORD or SEMANTIC mode. Then the system can do SEMANTIC_ANALYSIS on the results, to determine if it fits the comparison affirm or negate, and be included based on it's cosine similarity to them.\n"
        "The system will then either return an exhaustive list of finite results, or include only the most relevant results.\n"
        "Exhaustive lists are computationally expensive, so they should be used only upon user request.\n"
        "The following are the rules for the InformationSetParameters:\n"
        "- If the query strings represent a literal symbol name that is provided in the user request or message history, then the query type should be EXACT_MATCH_KEYWORD, else it should be SEMANTIC.\n"
        "- If the ElementAnalysis is SEMANTIC_ANALYSIS, then the comparison affirm and negate should be provided, else they should be null.\n"
        "- If the user request explicitly asks for a complete list of the information set, then the exhaustive should be ENFORCE_EXHAUSTIVENESS, else it should be either BEST_EFFORT or QUICK_AND_DIRTY, depending on whether the user request is asking for a specific information set, or if the system just needs a quick and dirty example.\n"
        "- If exhaustive is YES, then the bounding must be FINITE, because it is impossible to retrieve an exhausive list of information with an unbounded query.\n"
        "- If the query type is KEYWORD, the bounding must be FINITE, because there are only a certain number of instances of the keyword in the list of documents.\n"
        "- If the search results have additional qualifiers, then the ElementAnalysis should be SEMANTIC_ANALYSIS, else it should be ALL.\n"
        "- query strings are the strings that will be used to retrieve the information set via a search engine. These represent the keywords or concepts that that will retrieve information relevant to the information set.\n"
        "- bounding is the bounding of the information set.\n"
        "- comparison affirm is the rubrik to affirm that text in the query is relevant to the information set.\n"
        "- comparison negate is the rubrik to negate that text in the query is relevant to the information set.\n"
        "- If an element in the information set is more similar to the affirmation rubrik, then the query will be affirmed.\n"
        "- If an element in the information set is more similar to the negation rubrik, then the query will be negated.\n"
        "- query type is the type of query to be used.\n"
        "- element analysis is the analysis of the elements of the information set.\n"
        "- exhaustive is whether the information set is exhaustive.\n"
        "- rationale is the rationale for why the parameters were chosen.\n"
    )
    message_kind: MessageKind = MessageKind.SYSTEM


class GetInformationSetsParametersMessage(LlmMessage):
    message_kind: MessageKind = MessageKind.USER

    @classmethod
    def from_context(
        cls,
        prompt: str,
        information_set_name: str,
        information_set_description: str,
        information_set_rationale: str,
        selected_text: str | None = None,
    ) -> "GetInformationSetsUserMessage":
        content = (
            "Return the parameters for the information set retrieval."
            f"Information Set Name: {information_set_name}\n"
            f"Information Set Description: {information_set_description}\n"
            f"Information Set Rationale: {information_set_rationale}\n"
            "The following is the user request to be fulfilled:"
            f"{PROMPT_XML_BEGIN}{prompt}{PROMPT_XML_END}\n"
            f"{f'{USER_SELECTED_TEXT_XML_BEGIN}{selected_text}{USER_SELECTED_TEXT_XML_END}\n' if selected_text and selected_text.strip() else ''}"
        ).strip()
        return cls(content=content)
