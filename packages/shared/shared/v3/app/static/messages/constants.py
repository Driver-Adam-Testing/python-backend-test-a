# USER CONTEXT BASED XML TAGS
PROMPT_XML_BEGIN = "<PROMPT>"
PROMPT_XML_END = "</PROMPT>"

# PAGE CONTENT BASED XML TAGS
USER_SELECTED_TEXT_XML_BEGIN = "<USER_CURSOR_SELECTED_TEXT>"
USER_SELECTED_TEXT_XML_END = "</USER_CURSOR_SELECTED_TEXT>"
USER_CURSOR_XML_BEGIN = "<USER_CURSOR>"
USER_CURSOR_XML_END = "</USER_CURSOR>"
DOCUMENT_CONTENT_BEFORE_CURSOR_XML_BEGIN = "<DOCUMENT_CONTENT_BEFORE_CURSOR>"
DOCUMENT_CONTENT_BEFORE_CURSOR_XML_END = "</DOCUMENT_CONTENT_BEFORE_CURSOR>"
DOCUMENT_CONTENT_AFTER_CURSOR_XML_BEGIN = "<DOCUMENT_CONTENT_AFTER_CURSOR>"
DOCUMENT_CONTENT_AFTER_CURSOR_XML_END = "</DOCUMENT_CONTENT_AFTER_CURSOR>"

# REFERENCES XML TAGS
SEARCH_QUERY_XML_BEGIN = "<SEARCH_QUERY>"
SEARCH_QUERY_XML_END = "</SEARCH_QUERY>"
REFERENCE_XML_BEGIN = "<REFERENCE>"
REFERENCE_XML_END = "</REFERENCE>"
REFERENCE_CONTENT_XML_BEGIN = "<REFERENCE_CONTENT>"
REFERENCE_CONTENT_XML_END = "</REFERENCE_CONTENT>"
REFERENCE_PATH_XML_BEGIN = "<REFERENCE_PATH>"
REFERENCE_PATH_XML_END = "</REFERENCE_PATH>"
REFERENCES_XML_BEGIN = "<REFERENCES>"
REFERENCES_XML_END = "</REFERENCES>"
TOOL_ERROR_XML_BEGIN = "<TOOL_ERROR>"
TOOL_ERROR_XML_END = "</TOOL_ERROR>"

# LLM TEXT HELPERS
IMPORTANT = "!IMPORTANT!"


""" #TODO: Add a glossary to the system prompt to allow the LLMs to understand the user's request.
Glossary:
- PAGE INTERACTIONS
 - Cursor: The user's cursor in the document.
 - User: The user who is interacting with the system.
 - Document/Page: The document that the user is interacting with. WHAT DO WE CALL THIS?
 - Prompt: The user's prompt to the system.
 - Context?: The context of the document that the user is interacting with.
 - User Prompt: The user's prompt to the system.
 - User Selected Text: The text that the user has selected in the document.

- RETRIEVAL
 - InformationSet: A set of information that the user has provided to the system.
 - REFERENCES
 - Retrieval?
 - Internal vs external information
- AGENTIC CONTEXT
 - Internal vs external information
 - All the types of external information that exist in the system currently
"""
