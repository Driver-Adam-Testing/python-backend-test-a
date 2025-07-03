from utils.lang_specialization.ir_common import ListData
from utils.lang_specialization.python import (
    SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT,
    SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_PY,
    PyClassCollection,
    PyClassRawSymbolCollection,
    PyFnCollection,
    PyFnRawSymbolCollection,
    PyImportRawSymbolCollection,
    PyVariableCollection,
    PyVariableRawSymbolCollection,
)
from utils.prompts import (
    GENERAL_STE_STYLE_INSTRUCTION,
    NO_RESTATEMENT_STYLE_INSTRUCTION_FOR_CODE_PURPOSE,
    Component,
    Prompt,
)
from utils.templates import S

SOURCE_CODE_LARGE_TEMPLATE_PY = [
    (
        S.SINGLE_PROMPT_TEXT,
        "# Purpose",
        Prompt.empty()
        .append(Component(string=SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_PY))
        .append(GENERAL_STE_STYLE_INSTRUCTION)
        .into_str(),
        Prompt.empty()
        .append(Component(string=SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT))
        .append(NO_RESTATEMENT_STYLE_INSTRUCTION_FOR_CODE_PURPOSE)
        .into_str(),
    ),
    (
        S.FN_COND_JSON,
        "# Imports and Dependencies",
        PyImportRawSymbolCollection.from_static_analysis,
        lambda _llm, output, _code: ListData(data=list(output.data.keys())),
        None,
    ),
    (
        S.FN_COND_JSON,
        "# Global Variables",
        PyVariableRawSymbolCollection.from_static_analysis,
        PyVariableCollection.from_llm,
        None,
    ),
    (
        S.FN_COND_JSON,
        "# Classes",
        PyClassRawSymbolCollection.from_static_analysis,
        PyClassCollection.from_llm,
        None,
    ),
    (
        S.FN_COND_JSON,
        "# Functions",
        PyFnRawSymbolCollection.from_static_analysis,
        PyFnCollection.from_llm,
        None,
    ),
]
