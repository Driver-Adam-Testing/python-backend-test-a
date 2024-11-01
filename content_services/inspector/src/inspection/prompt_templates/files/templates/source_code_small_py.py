from utils.lang_specialization.default import default_imports_checker
from utils.lang_specialization.python import (
    SOURCE_CODE_SMALL_PURPOSE_USER_PROMPT,
    SOURCE_CODE_SMALL_SYSTEM_PROMPT_GENERAL_PY,
    PyClassRawSymbolCollection,
    PyFnRawSymbolCollection,
    PyVariableRawSymbolCollection,
    class_dict_from_llm_py,
    fn_dict_from_llm_py,
    variables_dict_from_llm_py,
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
        variables_dict_from_llm_py,
        None,
    ),
    (
        S.FN_COND_JSON,
        "# Classes",
        PyClassRawSymbolCollection.from_static_analysis,
        class_dict_from_llm_py,
        None,
    ),
    (
        S.FN_COND_JSON,
        "# Functions",
        PyFnRawSymbolCollection.from_static_analysis,
        fn_dict_from_llm_py,
        None,
    ),
]
