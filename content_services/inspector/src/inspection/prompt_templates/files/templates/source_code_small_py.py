from utils.lang_specialization.default import default_imports_checker
from utils.lang_specialization.python import (
    SOURCE_CODE_SMALL_PURPOSE_USER_PROMPT,
    SOURCE_CODE_SMALL_SYSTEM_PROMPT_GENERAL_PY,
    class_dict_from_llm_py,
    fn_dict_from_llm_py,
    py_class_checker,
    py_function_checker,
    py_variables_checker,
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
        py_variables_checker,
        variables_dict_from_llm_py,
        None,
    ),
    (
        S.FN_COND_JSON,
        "# Data Structures",
        py_class_checker,
        class_dict_from_llm_py,
        None,
    ),
    (
        S.FN_COND_JSON,
        "# Functions",
        py_function_checker,
        fn_dict_from_llm_py,
        None,
    ),
]
