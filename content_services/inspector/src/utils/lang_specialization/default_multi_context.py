from utils.lang_specialization.default import (
    DATA_STRUCTURES_CHECKER_SYSTEM_PROMPT_JSON,
    FUNCTIONS_CHECKER_SYSTEM_PROMPT_JSON,
    VARIABLES_CHECKER_SYSTEM_PROMPT_JSON,
    _default_checker,
)
from utils.models import ChatOpenAI

SOURCE_CODE_SYSTEM_PROMPT_GENERAL_DEFAULT_MULTI_CONTEXT = """
You are a software engineering documentation expert. You write detailed documentation to explain software.

You are skilled at explaining technical details as well as recognizing and articulating the key conceptual components and purpose of software.
"""

SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT_MULTI_CONTEXT = """
In a single paragraph of 3 to 5 sentences, explain the purpose of the code provided below. Consider questions such as the following when providing your output:

- Does this code provide narrow or broad functionality?
- Is this code a collection of many different components? If so, what is the common theme or purpose?
- What kind of code is this? For example, is this code clearly an executable (e.g., main.c), a header file, a library file intended to be imported elsewhere, a collection of configuration variables, etc.?
- Does it define public APIs or external interfaces?
"""

SOURCE_CODE_PURPOSE_FROM_CHUNKS = """
You will be provided two or more paragraphs describing the purpose of a overlapping chunks of source code.

In a single paragraph of 3 to 5 sentences, combine the multiple purpose paragraphs into a single cohesive paragraph that describes the purpose of the entire code.
"""

TECHNICAL_CONCEPTS_MULTI_CONTEXT = """
In a single paragraph of 3 to 5 sentences, describe the important technical features and their interactions in the code provided below.

In writing your description, write about about the conceptual use cases, applications, logic, and component interactions instead of focusing on particular functions, variables, etc.
"""

TECHNICAL_CONCEPTS_FROM_CHUNKS = """
You will be provided two or more paragraphs describing the technical concepts of overlapping chunks of source code.

In a single paragraph of 3 to 5 sentences, combine the multiple technical concept paragraphs into a single cohesive paragraph that describes the technical concepts of the entire code.
"""


def default_variable_checker_multi_prompt(
    llm: ChatOpenAI, code_chunks: list[str]
) -> list[int, list[str]] | None:
    checker_responses = []
    for idx, code_chunk in enumerate(code_chunks):
        response_data = _default_checker(
            llm=llm,
            user_prompt="",
            system_prompt=VARIABLES_CHECKER_SYSTEM_PROMPT_JSON,
            code=code_chunk,
        )
        if response_data is not None:
            checker_responses.append([idx, response_data])
    if len(checker_responses) > 0:
        # Dedupe entities assuming we have chunk overlap
        for idx in range(len(checker_responses[:-1])):
            overlap_vars = set(checker_responses[idx][1]) & set(
                checker_responses[idx + 1][1]
            )
            checker_responses[idx][1] = list(
                set(checker_responses[idx][1]) - overlap_vars
            )
        return checker_responses
    else:
        return None


def default_data_structure_checker_multi_prompt(
    llm: ChatOpenAI, code_chunks: list[str]
) -> list[int, list[str]] | None:
    checker_responses = []
    for idx, code_chunk in enumerate(code_chunks):
        response_data = _default_checker(
            llm=llm,
            user_prompt="",
            system_prompt=DATA_STRUCTURES_CHECKER_SYSTEM_PROMPT_JSON,
            code=code_chunk,
        )
        if response_data is not None:
            checker_responses.append([idx, response_data])
    if len(checker_responses) > 0:
        # Dedupe entities assuming we have chunk overlap
        for idx in range(len(checker_responses[:-1])):
            overlap_ds = set(checker_responses[idx][1]) & set(
                checker_responses[idx + 1][1]
            )
            checker_responses[idx][1] = list(
                set(checker_responses[idx][1]) - overlap_ds
            )
        return checker_responses
    else:
        return None


def default_function_checker_multi_prompt(
    llm: ChatOpenAI, code_chunks: list[str]
) -> list[int, list[str]] | None:
    checker_responses = []
    for idx, code_chunk in enumerate(code_chunks):
        response_data = _default_checker(
            llm=llm,
            user_prompt="",
            system_prompt=FUNCTIONS_CHECKER_SYSTEM_PROMPT_JSON,
            code=code_chunk,
        )
        if response_data is not None:
            checker_responses.append([idx, response_data])
    if len(checker_responses) > 0:
        # Dedupe entities assuming we have chunk overlap
        for idx in range(len(checker_responses[:-1])):
            overlap_fns = set(checker_responses[idx][1]) & set(
                checker_responses[idx + 1][1]
            )
            checker_responses[idx][1] = list(
                set(checker_responses[idx][1]) - overlap_fns
            )
        return checker_responses
    else:
        return None
