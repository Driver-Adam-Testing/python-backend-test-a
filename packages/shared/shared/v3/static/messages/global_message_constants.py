# USER CONTEXT BASED XML TAGS
PROMPT_XML_BEGIN = "<PROMPT>"
PROMPT_XML_END = "</PROMPT>"
USER_SELECTED_TEXT_XML_BEGIN = "<USER_CURSOR_SELECTED_TEXT>"
USER_SELECTED_TEXT_XML_END = "</USER_CURSOR_SELECTED_TEXT>"
USER_CURSOR_XML_BEGIN = "<USER_CURSOR>"
USER_CURSOR_XML_END = "</USER_CURSOR>"

# PAGE CONTENT BASED XML TAGS
DOCUMENT_CONTENT_BEFORE_CURSOR_XML_BEGIN = "<DOCUMENT_CONTENT_BEFORE_CURSOR>"
DOCUMENT_CONTENT_BEFORE_CURSOR_XML_END = "</DOCUMENT_CONTENT_BEFORE_CURSOR>"
DOCUMENT_CONTENT_AFTER_CURSOR_XML_BEGIN = "<DOCUMENT_CONTENT_AFTER_CURSOR>"
DOCUMENT_CONTENT_AFTER_CURSOR_XML_END = "</DOCUMENT_CONTENT_AFTER_CURSOR>"

# REFERENCES XML TAGS
EXTERNAL_REFERENCE_XML_BEGIN = "<EXTERNAL_REFERENCE>"
EXTERNAL_REFERENCE_XML_END = "</EXTERNAL_REFERENCE>"
EXTERNAL_REFERENCE_CONTENT_XML_BEGIN = "<EXTERNAL_REFERENCE_CONTENT>"
EXTERNAL_REFERENCE_CONTENT_XML_END = "</EXTERNAL_REFERENCE_CONTENT>"
EXTERNAL_REFERENCE_ID_XML_BEGIN = "<EXTERNAL_REFERENCE_ID>"
EXTERNAL_REFERENCE_ID_XML_END = "</EXTERNAL_REFERENCE_ID>"
EXTERNAL_REFERENCE_PATH_XML_BEGIN = "<EXTERNAL_REFERENCE_PATH>"
EXTERNAL_REFERENCE_PATH_XML_END = "</EXTERNAL_REFERENCE_PATH>"
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
 - Retrieval?
 - Internal vs external information
- AGENTIC CONTEXT
 - Internal vs external information
 - All the types of external information that exist in the system currently
"""
