from shared.prompts.structured_prompting import (
    GENERAL_STE_STYLE_INSTRUCTION,
    NO_RESTATEMENT_STYLE_INSTRUCTION_FOR_CODE_PURPOSE,
    USE_BACKTICKS_STYLE_INSTRUCTION,
    Component,
    Prompt,
)
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
        Prompt.empty()
        .append(Component(string=SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_JS_TS))
        .append(GENERAL_STE_STYLE_INSTRUCTION)
        .append(USE_BACKTICKS_STYLE_INSTRUCTION)
        .into_str(),
        Prompt.empty()
        .append(Component(string=SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT))
        .append(NO_RESTATEMENT_STYLE_INSTRUCTION_FOR_CODE_PURPOSE)
        .into_str(),
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
