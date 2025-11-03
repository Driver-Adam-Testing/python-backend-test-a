from shared.inspector.utils.lang_specialization.default import (
    IMPORTS_SYSTEM_PROMPT_JSON,
    _default_checker,
)
from shared.inspector.utils.models import ChatOpenAI

SOURCE_CODE_SYSTEM_PROMPT_GENERAL_DEFAULT_MULTI_CONTEXT = """
You are a software engineering documentation expert. You write detailed documentation to explain software.

You are skilled at explaining technical details as well as recognizing and articulating the key conceptual components and purpose of software.
"""

SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT_MULTI_CONTEXT = """
In 1 to 3 paragraphs, explain the purpose of the code provided below. Consider questions such as the following when providing your output:

- Does this code provide narrow or broad functionality?
- Is this code a collection of many different components? If so, what is the common theme or purpose?
- What kind of code is this? For example, is this code clearly an executable (e.g., main.c), a header file, a library file intended to be imported elsewhere, a collection of configuration variables, etc.?
- Does it define public APIs or external interfaces?
"""

SOURCE_CODE_PURPOSE_FROM_CHUNKS = """
You will be provided two or more paragraphs describing the purpose of a overlapping chunks of source code.

In a single paragraph of 3 to 5 sentences, combine the multiple purpose paragraphs into a single cohesive paragraph that describes the purpose of the entire code.
"""


def default_imports_checker_multi_prompt(
    llm: ChatOpenAI, code_chunks: list[str], root_rel_path: str
) -> list[str] | None:
    return _default_checker(
        llm=llm,
        user_prompt="",
        system_prompt=IMPORTS_SYSTEM_PROMPT_JSON,
        code=code_chunks[0],
        as_list_data_ds=True,
    )
