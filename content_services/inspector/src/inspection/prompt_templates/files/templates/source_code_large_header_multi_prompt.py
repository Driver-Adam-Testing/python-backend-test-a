from utils.lang_specialization.default_multi_context import (
    SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT_MULTI_CONTEXT,
    SOURCE_CODE_PURPOSE_FROM_CHUNKS,
    default_imports_checker_multi_prompt,
)
from utils.lang_specialization.header import (
    SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_C_OR_CPP_HEADER,
    HeaderDataStructureRawSymbolCollection,
    HeaderFnRawSymbolCollection,
    HeaderVariableRawSymbolCollection,
    class_dict_from_llm_header,
    fn_dict_from_llm_header,
    variables_dict_from_llm_header,
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
        variables_dict_from_llm_header,
        None,
    ),
    (
        S.FN_COND_JSON,
        "# Data Structures",
        HeaderDataStructureRawSymbolCollection.from_static_analysis,
        class_dict_from_llm_header,
        None,
    ),
    (
        S.FN_COND_JSON,
        "# Functions",
        HeaderFnRawSymbolCollection.from_static_analysis,
        fn_dict_from_llm_header,
        None,
    ),
]
