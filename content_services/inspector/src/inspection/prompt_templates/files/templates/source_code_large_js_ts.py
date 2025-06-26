from utils.lang_specialization.ir_common import ListData
from utils.lang_specialization.js_ts import (
    SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT,
    SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_JS_TS,
    JsTsClassCollection,
    JsTsClassRawSymbolCollection,
    JsTsFnCollection,
    JsTsFnRawSymbolCollection,
    JsTsImportRawSymbolCollection,
    JsTsInterfaceCollection,
    JsTsInterfaceRawSymbolCollection,
    JsTsTypeCollection,
    JsTsTypeRawSymbolCollection,
    JsTsVariableCollection,
    JsTsVariableRawSymbolCollection,
)
from utils.templates import S

SOURCE_CODE_LARGE_TEMPLATE_JS_TS = [
    (
        S.SINGLE_PROMPT_TEXT,
        "# Purpose",
        SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_JS_TS,
        SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT,
    ),
    (
        S.FN_COND_JSON,
        "# Imports and Dependencies",
        JsTsImportRawSymbolCollection.from_static_analysis,
        lambda _llm, output, _code: ListData(data=list(output.data.keys())),
        None,
    ),
    (
        S.FN_COND_JSON,
        "# Global Variables",
        JsTsVariableRawSymbolCollection.from_static_analysis,
        JsTsVariableCollection.from_llm,
        None,
    ),
    (
        S.FN_COND_JSON,
        "# Classes",
        JsTsClassRawSymbolCollection.from_static_analysis,
        JsTsClassCollection.from_llm,
        None,
    ),
    (
        S.FN_COND_JSON,
        "# Interfaces",
        JsTsInterfaceRawSymbolCollection.from_static_analysis,
        JsTsInterfaceCollection.from_llm,
        None,
    ),
    (
        S.FN_COND_JSON,
        "# Types",
        JsTsTypeRawSymbolCollection.from_static_analysis,
        JsTsTypeCollection.from_llm,
        None,
    ),
    (
        S.FN_COND_JSON,
        "# Functions",
        JsTsFnRawSymbolCollection.from_static_analysis,
        JsTsFnCollection.from_llm,
        None,
    ),
]
