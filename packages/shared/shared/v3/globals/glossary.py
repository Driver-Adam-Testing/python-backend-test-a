class GlossaryDefinition:
    def __init__(self, name: str, tag: str, description: str) -> None:
        self.name = name
        self.tag = tag
        self.description = description

    @property
    def xml_begin(self) -> str:
        return f"<{self.tag}>"

    @property
    def xml_end(self) -> str:
        return f"</{self.tag}>"

    def wrap(self, text: str | None, annotate_empty: bool = False) -> str:
        if text is None or text == "":
            if annotate_empty:
                return f"{self.xml_begin}{self.xml_end}"
            return ""
        return f"{self.xml_begin}\n\t{text}\n{self.xml_end}\n"


# USER INTERACTION DEFINITIONS
USER_PROMPT = GlossaryDefinition(
    "user prompt",
    "USER_PROMPT",
    "The user prompt is the prompt that the user has entered.",
)

# CURSOR DEFINITIONS
CURSOR = GlossaryDefinition(
    "cursor",
    "CURSOR",
    "The cursor is the position of the user's cursor in the document.",
)
CURSOR_SELECTION = GlossaryDefinition(
    "cursor selection",
    "CURSOR_SELECTION",
    "The cursor selection is the area of a document that is selected by the cursor",
)
DOCUMENT_CONTENT_BEFORE_CURSOR = GlossaryDefinition(
    "document content before cursor",
    "DOCUMENT_CONTENT_BEFORE_CURSOR",
    "The document content before the cursor is the text that is before the cursor in the document.",
)
DOCUMENT_CONTENT_AFTER_CURSOR = GlossaryDefinition(
    "document content after cursor",
    "DOCUMENT_CONTENT_AFTER_CURSOR",
    "The document content after the cursor is the text that is after the cursor in the document.",
)

# DOCUMENT DEFINITIONS
WORKING_DOCUMENT = GlossaryDefinition(
    "working document",
    "WORKING_DOCUMENT",
    "The working document is the document that the user is interacting with and editing.",
)
WORKING_DOCUMENT_CONTENT = GlossaryDefinition(
    "working document content",
    "WORKING_DOCUMENT_CONTENT",
    "The working document content is the content of the working document.",
)


# REFERENCE DEFINITIONS
REFERENCE_LIST = GlossaryDefinition(
    "reference list",
    "REFERENCE_LIST",
    "The reference list is the list of references that have been retrieved for the assistant.",
)
REFERENCE = GlossaryDefinition(
    "reference",
    "REFERENCE",
    "The reference is a single reference that has been retrieved for the assistant.",
)
REFERENCE_CONTENT = GlossaryDefinition(
    "reference content",
    "REFERENCE_CONTENT",
    "The reference content is the content of the reference that has been retrieved for the assistant.",
)
REFERENCE_RELATIVE_PATH = GlossaryDefinition(
    "reference relative path",
    "REFERENCE_RELATIVE_PATH",
    "The reference relative path is the relative path of the reference that has been retrieved for the assistant.",
)
REFERENCE_LINE_NUMBER = GlossaryDefinition(
    "reference line number",
    "REFERENCE_LINE_NUMBER",
    "The reference line number is the line number of the reference that has been retrieved for the assistant.",
)

# TOOL DEFINITIONS
TOOL_ERROR_MESSAGE = GlossaryDefinition(
    "tool error message",
    "TOOL_ERROR_MESSAGE",
    "The tool error message is the message that the tool has returned.",
)

# SEARCH DEFINITIONS
SEARCH_QUERY = GlossaryDefinition(
    "search query",
    "SEARCH_QUERY",
    "The search query is the query.",
)


# COPY EDITOR DEFINITIONS
TEXT_TO_EDIT = GlossaryDefinition(
    "text to edit",
    "TEXT_TO_EDIT",
    "The text to edit is the text that the user wants to edit.",
)

# DATA SOURCE DEFINITIONS
DATA_SOURCES = GlossaryDefinition(
    "data sources",
    "DATA_SOURCES",
    "The data sources are the data sources that are available to the assistant via tools.",
)

TOOL_RESPONSE_CONTENT_JSON = GlossaryDefinition(
    "tool response content json",
    "TOOL_RESPONSE_CONTENT_JSON",
    "The 'tool response content json' is content of the tool response that has been retrieved for the assistant in JSON format.",
)

TOOL_RESPONSE_CONTENT_MARKDOWN = GlossaryDefinition(
    "tool response content markdown",
    "TOOL_RESPONSE_CONTENT_MARKDOWN",
    "The 'tool response content markdown' is content of the tool response that has been retrieved for the assistant in markdown format.",
)

TOOL_RESPONSE_CONTENT_YAML = GlossaryDefinition(
    "tool response content yaml",
    "TOOL_RESPONSE_CONTENT_YAML",
    "The 'tool response content yaml' is content of the tool response that has been retrieved for the assistant in YAML format.",
)
