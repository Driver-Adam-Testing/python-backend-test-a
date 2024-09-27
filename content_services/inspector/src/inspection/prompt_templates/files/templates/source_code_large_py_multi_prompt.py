from utils.lang_specialization.common import classes_dict_from_llm_multi_prompt
from utils.lang_specialization.default_multi_context import (
    SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT_MULTI_CONTEXT,
    SOURCE_CODE_PURPOSE_FROM_CHUNKS,
    default_imports_checker_multi_prompt,
)
from utils.lang_specialization.python import (
    SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_PY,
    fn_dict_from_llm_py_multi_prompt,
    py_class_checker,
    py_function_checker,
    py_variables_checker,
    variables_dict_from_llm_py_multi_prompt,
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
        py_variables_checker,
        variables_dict_from_llm_py_multi_prompt,
        None,
    ),
    (
        S.FN_COND_JSON,
        "# Classes",
        py_class_checker,
        classes_dict_from_llm_multi_prompt,
        None,
    ),
    (
        S.FN_COND_JSON,
        "# Functions",
        py_function_checker,
        fn_dict_from_llm_py_multi_prompt,
        None,
    ),
]
