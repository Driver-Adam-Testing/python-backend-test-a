from utils.lang_specialization.c import (
    SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_C,
    c_data_structure_checker,
    c_function_checker,
    c_variables_checker,
    data_structure_dict_from_llm_c_multi_prompt,
    fn_dict_from_llm_c_multi_prompt,
    variables_dict_from_llm_c_multi_prompt,
)
from utils.lang_specialization.default_multi_context import (
    SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT_MULTI_CONTEXT,
    SOURCE_CODE_PURPOSE_FROM_CHUNKS,
    default_imports_checker_multi_prompt,
)
from utils.templates import S

SOURCE_CODE_LARGE_MULTI_PROMPT_TEMPLATE_C = [
    (
        S.MULTI_PROMPT_TEXT,
        "# Purpose",
        SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_C,
        SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT_MULTI_CONTEXT,
        SOURCE_CODE_PURPOSE_FROM_CHUNKS,
    ),
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
        c_variables_checker,
        variables_dict_from_llm_c_multi_prompt,
        None,
    ),
    (
        S.FN_COND_JSON,
        "# Data Structures",
        c_data_structure_checker,
        data_structure_dict_from_llm_c_multi_prompt,
        None,
    ),
    (
        S.FN_COND_JSON,
        "# Functions",
        c_function_checker,
        fn_dict_from_llm_c_multi_prompt,
        None,
    ),
]
