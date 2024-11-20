from utils.lang_specialization.cpp import (
    SOURCE_CODE_SMALL_PURPOSE_USER_PROMPT,
    SOURCE_CODE_SMALL_SYSTEM_PROMPT_GENERAL_CPP,
    CppClassCollection,
    CppClassRawSymbolCollection,
    CppFnCollection,
    CppFreeFnRawSymbolCollection,
    CppVariableCollection,
    CppVariableRawSymbolCollection,
)
from utils.lang_specialization.default import default_imports_checker
from utils.templates import S

SOURCE_CODE_SMALL_TEMPLATE_CPP = [
    (
        S.SINGLE_PROMPT_TEXT,
        "# Purpose",
        SOURCE_CODE_SMALL_SYSTEM_PROMPT_GENERAL_CPP,
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
        S.FN_COND_JSON,
        "# Global Variables",
        CppVariableRawSymbolCollection.from_static_analysis,
        CppVariableCollection.from_llm,
        None,
    ),
    (
        S.FN_COND_JSON,
        "# Data Structures",
        CppClassRawSymbolCollection.from_static_analysis,
        CppClassCollection.from_llm,
        None,
    ),
    (
        S.FN_COND_JSON,
        "# Functions",
        CppFreeFnRawSymbolCollection.from_static_analysis,
        CppFnCollection.from_llm,
        None,
    ),
]
