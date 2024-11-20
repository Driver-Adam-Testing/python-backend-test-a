from utils.lang_specialization.default_multi_context import (
    SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT_MULTI_CONTEXT,
    SOURCE_CODE_PURPOSE_FROM_CHUNKS,
    default_imports_checker_multi_prompt,
)
from utils.lang_specialization.header import (
    SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_C_OR_CPP_HEADER,
    HeaderDataStructureCollection,
    HeaderDataStructureRawSymbolCollection,
    HeaderFnCollection,
    HeaderFnRawSymbolCollection,
    HeaderVariableCollection,
    HeaderVariableRawSymbolCollection,
)
from utils.templates import S

SOURCE_CODE_LARGE_MULTI_PROMPT_TEMPLATE_HEADER = [
    (
        S.MULTI_PROMPT_TEXT,
        "# Purpose",
        SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_C_OR_CPP_HEADER,
        SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT_MULTI_CONTEXT,
        SOURCE_CODE_PURPOSE_FROM_CHUNKS,
    ),
    (
        S.MULTI_LLM_COND_JSON,
        "# Imports and Dependencies",
        default_imports_checker_multi_prompt,
        lambda _llm, output, _code: output,
        None,
    ),
    (
        S.FN_COND_JSON,
        "# Global Variables",
        HeaderVariableRawSymbolCollection.from_static_analysis,
        HeaderVariableCollection.dict_from_llm,
        None,
    ),
    (
        S.FN_COND_JSON,
        "# Data Structures",
        HeaderDataStructureRawSymbolCollection.from_static_analysis,
        HeaderDataStructureCollection.dict_from_llm,
        None,
    ),
    (
        S.FN_COND_JSON,
        "# Functions",
        HeaderFnRawSymbolCollection.from_static_analysis,
        HeaderFnCollection.dict_from_llm,
        None,
    ),
]
