class GlossaryDefinition:
    def __init__(self, name: str, description: str) -> None:
        self.name = name
        self.description = description

    @property
    def xml_begin(self) -> str:
        return f"<{self.name}>"

    @property
    def xml_end(self) -> str:
        return f"</{self.name}>"

    def wrap(self, text: str | None, annotate_empty: bool = False) -> str:
        if text is None or text == "":
            if annotate_empty:
                return f"{self.xml_begin}{self.xml_end}"
            return ""
        return f"{self.xml_begin}\n\t{text}\n{self.xml_end}\n"


# USER INTERACTION DEFINITIONS
USER_PROMPT = GlossaryDefinition(
    "USER_PROMPT", "The user prompt is the prompt that the user has entered."
)

# CURSOR DEFINITIONS
CURSOR = GlossaryDefinition(
    "CURSOR", "The cursor is the position of the user's cursor in the document."
)
CURSOR_SELECTION = GlossaryDefinition(
    "CURSOR_SELECTION",
    "The cursor selection is the text that the user has selected in the document.",
)
DOCUMENT_CONTENT_BEFORE_CURSOR = GlossaryDefinition(
    "DOCUMENT_CONTENT_BEFORE_CURSOR",
    "The document content before the cursor is the text that is before the cursor in the document.",
)
DOCUMENT_CONTENT_AFTER_CURSOR = GlossaryDefinition(
    "DOCUMENT_CONTENT_AFTER_CURSOR",
    "The document content after the cursor is the text that is after the cursor in the document.",
)

# DOCUMENT DEFINITIONS
WORKING_DOCUMENT = GlossaryDefinition(
    "WORKING_DOCUMENT",
    "The working document is the document that the user is interacting with and editing.",
)
DOCUMENT_CONTENT = GlossaryDefinition(
    "DOCUMENT_CONTENT",
    "The document content is the content of the working document.",
)


# REFERENCE DEFINITIONS
REFERENCE_LIST = GlossaryDefinition(
    "REFERENCE_LIST",
    "The reference list is the list of references that have been retrieved for the assistant.",
)
REFERENCE = GlossaryDefinition(
    "REFERENCE",
    "The reference is a single reference that has been retrieved for the assistant.",
)
REFERENCE_CONTENT = GlossaryDefinition(
    "REFERENCE_CONTENT",
    "The reference content is the content of the reference that has been retrieved for the assistant.",
)
REFERENCE_RELATIVE_PATH = GlossaryDefinition(
    "REFERENCE_RELATIVE_PATH",
    "The reference relative path is the relative path of the reference that has been retrieved for the assistant.",
)
REFERENCE_LINE_NUMBER = GlossaryDefinition(
    "REFERENCE_LINE_NUMBER",
    "The reference line number is the line number of the reference that has been retrieved for the assistant.",
)

# TOOL DEFINITIONS
TOOL_ERROR_MESSAGE = GlossaryDefinition(
    "TOOL_ERROR_MESSAGE",
    "The tool error message is the message that the tool has returned.",
)

# SEARCH DEFINITIONS
SEARCH_QUERY = GlossaryDefinition(
    "SEARCH_QUERY",
    "The search query is the query.",
)


# COPY EDITOR DEFINITIONS
TEXT_TO_EDIT = GlossaryDefinition(
    "TEXT_TO_EDIT",
    "The text to edit is the text that the user wants to edit.",
)

# DATA SOURCE DEFINITIONS
DATA_SOURCES = GlossaryDefinition(
    "DATA_SOURCES",
    "The data sources are the data sources that are available to the assistant via tools.",
)
