from shared.inspector.utils.lang_specialization.cpp import (
    SOURCE_CODE_SMALL_PURPOSE_USER_PROMPT,
    SOURCE_CODE_SMALL_SYSTEM_PROMPT_GENERAL_CPP,
    CppDataStructureCollection,
    CppDataStructureRawSymbolCollection,
    CppFnCollection,
    CppFreeFnRawSymbolCollection,
    CppIncludeRawSymbolCollection,
    CppVariableCollection,
    CppVariableRawSymbolCollection,
)
from shared.inspector.utils.lang_specialization.ir_common import ListData
from shared.inspector.utils.templates import S
from shared.prompts.structured_prompting import (
    GENERAL_STE_STYLE_INSTRUCTION,
    NO_RESTATEMENT_STYLE_INSTRUCTION_FOR_CODE_PURPOSE,
    USE_BACKTICKS_STYLE_INSTRUCTION,
    Component,
    Prompt,
)

SOURCE_CODE_SMALL_TEMPLATE_CPP = [
    (
        S.SINGLE_PROMPT_TEXT,
        "# Purpose",
        Prompt.empty()
        .append(Component(string=SOURCE_CODE_SMALL_SYSTEM_PROMPT_GENERAL_CPP))
        .append(GENERAL_STE_STYLE_INSTRUCTION)
        .append(USE_BACKTICKS_STYLE_INSTRUCTION)
        .into_str(),
        Prompt.empty()
        .append(Component(string=SOURCE_CODE_SMALL_PURPOSE_USER_PROMPT))
        .append(NO_RESTATEMENT_STYLE_INSTRUCTION_FOR_CODE_PURPOSE)
        .into_str(),
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
