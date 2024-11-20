from utils.lang_specialization.default import default_imports_checker
from utils.lang_specialization.python import (
    SOURCE_CODE_SMALL_PURPOSE_USER_PROMPT,
    SOURCE_CODE_SMALL_SYSTEM_PROMPT_GENERAL_PY,
    PyClassCollection,
    PyClassRawSymbolCollection,
    PyFnCollection,
    PyFnRawSymbolCollection,
    PyVariableCollection,
    PyVariableRawSymbolCollection,
)
from utils.templates import S

SOURCE_CODE_SMALL_TEMPLATE_PY = [
    (
        S.SINGLE_PROMPT_TEXT,
        "# Purpose",
        SOURCE_CODE_SMALL_SYSTEM_PROMPT_GENERAL_PY,
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
