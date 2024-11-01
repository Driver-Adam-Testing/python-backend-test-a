from utils.lang_specialization.default_multi_context import (
    SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT_MULTI_CONTEXT,
    SOURCE_CODE_PURPOSE_FROM_CHUNKS,
    default_imports_checker_multi_prompt,
)
from utils.lang_specialization.python import (
    SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_PY,
    PyClassRawSymbolCollection,
    PyFnRawSymbolCollection,
    PyVariableRawSymbolCollection,
    class_dict_from_llm_py,
    fn_dict_from_llm_py,
    variables_dict_from_llm_py,
)
from utils.templates import S

SOURCE_CODE_LARGE_MULTI_PROMPT_TEMPLATE_PY = [
    (
        S.MULTI_PROMPT_TEXT,
        "# Purpose",
        SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_PY,
        SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT_MULTI_CONTEXT,
        SOURCE_CODE_PURPOSE_FROM_CHUNKS,
    ),
    # NOTE: for simplicity this only looks at the first file chunk for imports (making assumptions about the structure of the file)
    (
        S.MULTI_LLM_COND_JSON,
        "# Imports and Dependencies",
        default_imports_checker_multi_prompt,
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
