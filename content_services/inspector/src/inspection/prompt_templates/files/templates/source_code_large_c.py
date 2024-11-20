from utils.lang_specialization.c import (
    SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT,
    SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_C,
    CDataStructureCollection,
    CDataStructureRawSymbolCollection,
    CFunctionCollection,
    CFunctionRawSymbolCollection,
    CVariableCollection,
    CVariableRawSymbolCollection,
)
from utils.lang_specialization.default import (
    default_imports_checker,
)
from utils.templates import S

SOURCE_CODE_LARGE_TEMPLATE_C = [
    (
        S.SINGLE_PROMPT_TEXT,
        "# Purpose",
        SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_C,
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
        CVariableRawSymbolCollection.from_static_analysis,
        CVariableCollection.dict_from_llm,
        None,
    ),
    (
        S.FN_COND_JSON,
        "# Data Structures",
        CDataStructureRawSymbolCollection.from_static_analysis,
        CDataStructureCollection.dict_from_llm,
        None,
    ),
    (
        S.FN_COND_JSON,
        "# Functions",
        CFunctionRawSymbolCollection.from_static_analysis,
        CFunctionCollection.dict_from_llm,
        None,
    ),
]
