from utils.lang_specialization.default import (
    SOURCE_CODE_SMALL_PURPOSE_USER_PROMPT,
    SOURCE_CODE_SYSTEM_PROMPT_GENERAL_DEFAULT,
    DefaultDataStructureCollection,
    DefaultDataStructureRawSymbolCollection,
    DefaultFnCollection,
    DefaultFnRawSymbolCollection,
    DefaultVariableCollection,
    DefaultVariableRawSymbolCollection,
    default_imports_checker,
)
from utils.templates import S

SOURCE_CODE_SMALL_TEMPLATE_DEFAULT = [
    (
        S.SINGLE_PROMPT_TEXT,
        "# Purpose",
        SOURCE_CODE_SYSTEM_PROMPT_GENERAL_DEFAULT,
        SOURCE_CODE_SMALL_PURPOSE_USER_PROMPT,
    ),
    (
        S.LLM_COND_JSON,
        "# Imports and Dependencies",
        default_imports_checker,
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
