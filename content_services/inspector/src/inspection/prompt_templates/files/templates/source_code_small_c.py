from utils.lang_specialization.c import (
    SOURCE_CODE_SMALL_PURPOSE_USER_PROMPT,
    SOURCE_CODE_SMALL_SYSTEM_PROMPT_GENERAL_C,
    c_data_structure_checker,
    c_function_checker,
    c_variables_checker,
    data_structure_dict_from_llm_c,
    fn_dict_from_llm_c,
    variables_dict_from_llm_c,
)
from utils.lang_specialization.default import default_imports_checker
from utils.templates import S

SOURCE_CODE_SMALL_TEMPLATE_C = [
    (
        S.SINGLE_PROMPT_TEXT,
        "# Purpose",
        SOURCE_CODE_SMALL_SYSTEM_PROMPT_GENERAL_C,
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
        c_variables_checker,
        variables_dict_from_llm_c,
        None,
    ),
    (
        S.FN_COND_JSON,
        "# Data Structures",
        c_data_structure_checker,
        data_structure_dict_from_llm_c,
        None,
    ),
    (
        S.FN_COND_JSON,
        "# Functions",
        c_function_checker,
        fn_dict_from_llm_c,
        None,
    ),
]
