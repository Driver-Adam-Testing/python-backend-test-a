from utils.lang_specialization.default import (
    SOURCE_CODE_SMALL_PURPOSE_USER_PROMPT,
    SOURCE_CODE_SYSTEM_PROMPT_GENERAL_DEFAULT,
    data_structure_dict_from_llm_default,
    default_data_structure_checker,
    default_function_checker,
    default_imports_checker,
    default_variable_checker,
    fn_dict_from_llm_default,
    variables_dict_from_llm_default,
)
from utils.templates import S

SOURCE_CODE_SMALL_TEMPLATE_DEFAULT = [
    (
        S.SINGLE_PROMPT_TEXT,
        "# Purpose",
        SOURCE_CODE_SYSTEM_PROMPT_GENERAL_DEFAULT,
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
        S.LLM_COND_JSON,
        "# Global Variables",
        default_variable_checker,
        variables_dict_from_llm_default,
        None,
    ),
    (
        S.LLM_COND_JSON,
        "# Data Structures",
        default_data_structure_checker,
        data_structure_dict_from_llm_default,
        None,
    ),
    (
        S.LLM_COND_JSON,
        "# Functions",
        default_function_checker,
        fn_dict_from_llm_default,
        None,
    ),
]
