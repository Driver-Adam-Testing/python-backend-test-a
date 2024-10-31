from utils.lang_specialization.cpp import (
    SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT,
    SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_CPP,
    CppClassRawSymbolCollection,
    CppFreeFnRawSymbolCollection,
    CppVariableRawSymbolCollection,
    class_dict_from_llm_cpp,
    fn_dict_from_llm_cpp,
    variable_dict_from_llm_cpp,
)
from utils.lang_specialization.default import (
    default_imports_checker,
)
from utils.templates import S

SOURCE_CODE_LARGE_TEMPLATE_CPP = [
    (
        S.SINGLE_PROMPT_TEXT,
        "# Purpose",
        SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_CPP,
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
        CppVariableRawSymbolCollection.from_static_analysis,
        variable_dict_from_llm_cpp,
        None,
    ),
    (
        S.FN_COND_JSON,
        "# Data Structures",
        CppClassRawSymbolCollection.from_static_analysis,
        class_dict_from_llm_cpp,
        None,
    ),
    (
        S.FN_COND_JSON,
        "# Functions",
        CppFreeFnRawSymbolCollection.from_static_analysis,
        fn_dict_from_llm_cpp,
        None,
    ),
]
