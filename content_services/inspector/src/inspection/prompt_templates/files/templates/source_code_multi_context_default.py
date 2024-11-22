from utils.lang_specialization.default import (
    SOURCE_CODE_SYSTEM_PROMPT_GENERAL_DEFAULT,
    DefaultDataStructureCollection,
    DefaultDataStructureRawSymbolCollection,
    DefaultFnCollection,
    DefaultFnRawSymbolCollection,
    DefaultVariableCollection,
    DefaultVariableRawSymbolCollection,
)
from utils.lang_specialization.default_multi_context import (
    SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT_MULTI_CONTEXT,
    SOURCE_CODE_PURPOSE_FROM_CHUNKS,
    default_imports_checker_multi_prompt,
)
from utils.templates import S

SOURCE_CODE_MULTI_CONTEXT_TEMPLATE_DEFAULT = [
    (
        S.MULTI_PROMPT_TEXT,
        "# Purpose",
        SOURCE_CODE_SYSTEM_PROMPT_GENERAL_DEFAULT,
        SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT_MULTI_CONTEXT,
        SOURCE_CODE_PURPOSE_FROM_CHUNKS,
    ),
    # NOTE: for simplicity this only looks at the first file chunk for imports (making assumptions about the structure of the file)
    (
        S.MULTI_LLM_COND_JSON,
        "# Imports and Dependencies",
        default_imports_checker_multi_prompt,
        lambda _llm, output, _code: output,
        None,
    ),
    (
        S.MULTI_LLM_COND_JSON,
        "# Global Variables",
        DefaultVariableRawSymbolCollection.from_llm,
        DefaultVariableCollection.from_llm,
        None,
    ),
    (
        S.MULTI_LLM_COND_JSON,
        "# Data Structures",
        DefaultDataStructureRawSymbolCollection.from_llm,
        DefaultDataStructureCollection.from_llm,
        None,
    ),
    (
        S.MULTI_LLM_COND_JSON,
        "# Functions",
        DefaultFnRawSymbolCollection.from_llm,
        DefaultFnCollection.from_llm,
        None,
    ),
]
