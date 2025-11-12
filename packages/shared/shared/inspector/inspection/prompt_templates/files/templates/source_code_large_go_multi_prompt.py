from shared.inspector.utils.lang_specialization.default_multi_context import (
    SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT_MULTI_CONTEXT,
    SOURCE_CODE_PURPOSE_FROM_CHUNKS,
)
from shared.inspector.utils.lang_specialization.go import (
    SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_GO,
    GoCallableCollection,
    GoCallableRawSymbolCollection,
    GoDataStructureCollection,
    GoDataStructureRawSymbolCollection,
    GoImportRawSymbolCollection,
    GoInterfaceCollection,
    GoInterfaceRawSymbolCollection,
    GoVariableCollection,
    GoVariableGroupCollection,
    GoVariableGroupRawSymbolCollection,
    GoVariableRawSymbolCollection,
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

SOURCE_CODE_LARGE_MULTI_PROMPT_TEMPLATE_GO = [
    (
        S.MULTI_PROMPT_TEXT,
        "# Purpose",
        Prompt.empty()
        .append(Component(string=SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_GO))
        .append(GENERAL_STE_STYLE_INSTRUCTION)
        .append(USE_BACKTICKS_STYLE_INSTRUCTION)
        .into_str(),
        Prompt.empty()
        .append(Component(string=SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT_MULTI_CONTEXT))
        .append(NO_RESTATEMENT_STYLE_INSTRUCTION_FOR_CODE_PURPOSE)
        .into_str(),
        Prompt.empty()
        .append(Component(string=SOURCE_CODE_PURPOSE_FROM_CHUNKS))
        .append(NO_RESTATEMENT_STYLE_INSTRUCTION_FOR_CODE_PURPOSE)
        .into_str(),
    ),
    (
        S.FN_COND_JSON,
        "# Imports and Dependencies",
        GoImportRawSymbolCollection.from_static_analysis,
        lambda _llm, output, _code: ListData(data=list(output.data.keys())),
        None,
    ),
    (
        S.FN_COND_JSON,
        "# Global Variables and Constants",
        GoVariableRawSymbolCollection.from_static_analysis,
        GoVariableCollection.from_llm,
        None,
    ),
    (
        S.FN_COND_JSON,
        "# Variable and Constant Groups",
        GoVariableGroupRawSymbolCollection.from_static_analysis,
        GoVariableGroupCollection.from_llm,
        None,
    ),
    (
        S.FN_COND_JSON,
        "# Interfaces",
        GoInterfaceRawSymbolCollection.from_static_analysis,
        GoInterfaceCollection.from_llm,
        None,
    ),
    (
        S.FN_COND_JSON,
        "# Data Structures",
        GoDataStructureRawSymbolCollection.from_static_analysis,
        GoDataStructureCollection.from_llm,
        None,
    ),
    (
        S.FN_COND_JSON,
        "# Functions",
        GoCallableRawSymbolCollection.from_static_analysis,
        GoCallableCollection.from_llm,
        None,
    ),
]
