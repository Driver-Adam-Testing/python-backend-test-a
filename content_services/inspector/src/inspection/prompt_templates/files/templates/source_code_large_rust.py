from utils.lang_specialization.default import (
    default_imports_checker,
)
from utils.lang_specialization.rust import (
    SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT,
    SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_RUST,
    data_structure_dict_from_llm_rust,
    fn_dict_from_llm_rust,
    rust_data_structure_checker,
    rust_function_checker,
    rust_traits_checker,
    rust_variables_checker,
    traits_dict_from_llm_rust,
    variables_dict_from_llm_rust,
)
from utils.templates import S

SOURCE_CODE_LARGE_TEMPLATE_RUST = [
    (
        S.SINGLE_PROMPT_TEXT,
        "# Purpose",
        SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_RUST,
        SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT,
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
        rust_variables_checker,
        variables_dict_from_llm_rust,
        None,
    ),
    (
        S.FN_COND_JSON,
        "# Traits",
        rust_traits_checker,
        traits_dict_from_llm_rust,
        None,
    ),
    (
        S.FN_COND_JSON,
        "# Data Structures",
        rust_data_structure_checker,
        data_structure_dict_from_llm_rust,
        None,
    ),
    (
        S.FN_COND_JSON,
        "# Functions",
        rust_function_checker,
        fn_dict_from_llm_rust,
        None,
    ),
]
