from utils.lang_specialization.c import (
    SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT,
    SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_C,
    CDataStructureCollection,
    CDataStructureRawSymbolCollection,
    CDeclarationCollection,
    CDeclarationRawSymbolCollection,
    CFunctionCollection,
    CFunctionRawSymbolCollection,
    CIncludeRawSymbolCollection,
    CVariableCollection,
    CVariableRawSymbolCollection,
)
from utils.lang_specialization.ir_common import ListData
from utils.templates import S

SOURCE_CODE_LARGE_TEMPLATE_C = [
    (
        S.SINGLE_PROMPT_TEXT,
        "# Purpose",
        SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_C,
        SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT,
    ),
    (
        S.FN_COND_JSON,
        "# Imports and Dependencies",
        CIncludeRawSymbolCollection.from_static_analysis,
        lambda _llm, output, _code: ListData(data=list(output.data.keys())),
        None,
    ),
    (
        S.FN_COND_JSON,
        "# Global Variables",
        CVariableRawSymbolCollection.from_static_analysis,
        CVariableCollection.from_llm,
        None,
    ),
    (
        S.FN_COND_JSON,
        "# Data Structures",
        CDataStructureRawSymbolCollection.from_static_analysis,
        CDataStructureCollection.from_llm,
        None,
    ),
    (
        S.FN_COND_JSON,
        "# Functions",
        CFunctionRawSymbolCollection.from_static_analysis,
        CFunctionCollection.from_llm,
        None,
    ),
    (
        S.FN_COND_JSON,
        "# Function Declarations (Public API)",
        CDeclarationRawSymbolCollection.from_static_analysis,
        CDeclarationCollection.from_llm,
        None,
    ),
]
