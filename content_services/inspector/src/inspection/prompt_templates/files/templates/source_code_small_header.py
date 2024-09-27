from utils.lang_specialization.default import default_imports_checker
from utils.lang_specialization.header import (
    SOURCE_CODE_SMALL_PURPOSE_USER_PROMPT,
    SOURCE_CODE_SMALL_SYSTEM_PROMPT_GENERAL_C_OR_CPP_HEADER,
    class_dict_from_llm,
    fn_dict_from_llm_header,
    header_class_checker,
    header_function_checker,
    header_variables_checker,
    variables_dict_from_llm_header,
)
from utils.templates import S

SOURCE_CODE_SMALL_TEMPLATE_HEADER = [
    (
        S.SINGLE_PROMPT_TEXT,
        "# Purpose",
        SOURCE_CODE_SMALL_SYSTEM_PROMPT_GENERAL_C_OR_CPP_HEADER,
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
        header_variables_checker,
        variables_dict_from_llm_header,
        None,
    ),
    (
        S.FN_COND_JSON,
        "# Data Structures",
        header_class_checker,
        class_dict_from_llm,
        None,
    ),
    (
        S.FN_COND_JSON,
        "# Functions",
        header_function_checker,
        fn_dict_from_llm_header,
        None,
    ),
]
