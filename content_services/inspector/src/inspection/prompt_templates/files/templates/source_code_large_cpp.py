from utils.lang_specialization.cpp import (
    SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT,
    SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_CPP,
    CppDataStructureCollection,
    CppDataStructureRawSymbolCollection,
    CppFnCollection,
    CppFreeFnRawSymbolCollection,
    CppIncludeRawSymbolCollection,
    CppVariableCollection,
    CppVariableRawSymbolCollection,
)
from utils.lang_specialization.ir_common import ListData
from utils.templates import S

SOURCE_CODE_LARGE_TEMPLATE_CPP = [
    (
        S.SINGLE_PROMPT_TEXT,
        "# Purpose",
        SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_CPP,
        SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT,
    ),
    (
        S.FN_COND_JSON,
        "# Imports and Dependencies",
        CppIncludeRawSymbolCollection.from_static_analysis,
        lambda _llm, output, _code: ListData(data=list(output.data.keys())),
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
        CppDataStructureRawSymbolCollection.from_static_analysis,
        CppDataStructureCollection.from_llm,
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
