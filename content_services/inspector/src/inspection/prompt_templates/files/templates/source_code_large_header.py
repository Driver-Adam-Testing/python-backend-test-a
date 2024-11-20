from utils.lang_specialization.default import (
    default_imports_checker,
)
from utils.lang_specialization.header import (
    SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT,
    SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_C_OR_CPP_HEADER,
    HeaderDataStructureCollection,
    HeaderDataStructureRawSymbolCollection,
    HeaderFnCollection,
    HeaderFnRawSymbolCollection,
    HeaderVariableCollection,
    HeaderVariableRawSymbolCollection,
)
from utils.templates import S

SOURCE_CODE_LARGE_TEMPLATE_HEADER = [
    (
        S.SINGLE_PROMPT_TEXT,
        "# Purpose",
        SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_C_OR_CPP_HEADER,
        SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT,
    ),
    (
        S.LLM_COND_JSON,
        "# Imports and Dependencies",
        default_imports_checker,
        lambda _llm, output, _code: output,
        None,
    ),
    (
        S.FN_COND_JSON,
        "# Global Variables",
        HeaderVariableRawSymbolCollection.from_static_analysis,
        HeaderVariableCollection.from_llm,
        None,
    ),
    (
        S.FN_COND_JSON,
        "# Data Structures",
        HeaderDataStructureRawSymbolCollection.from_static_analysis,
        HeaderDataStructureCollection.from_llm,
        None,
    ),
    (
        S.FN_COND_JSON,
        "# Functions",
        HeaderFnRawSymbolCollection.from_static_analysis,
        HeaderFnCollection.from_llm,
        None,
    ),
]
