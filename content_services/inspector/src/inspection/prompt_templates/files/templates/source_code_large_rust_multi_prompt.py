from utils.lang_specialization.default_multi_context import (
    SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT_MULTI_CONTEXT,
    SOURCE_CODE_PURPOSE_FROM_CHUNKS,
    default_imports_checker_multi_prompt,
)
from utils.lang_specialization.rust import (
    SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_RUST,
    data_structure_dict_from_llm_rust_multi_prompt,
    fn_dict_from_llm_rust_multi_prompt,
    macros_dict_from_llm_rust_multi_prompt,
    rust_data_structure_checker,
    rust_function_checker,
    rust_macros_checker,
    rust_traits_checker,
    rust_variables_checker,
    traits_dict_from_llm_rust_multi_prompt,
    variables_dict_from_llm_rust_multi_prompt,
)
from utils.templates import S

SOURCE_CODE_LARGE_MULTI_PROMPT_TEMPLATE_RUST = [
    (
        S.MULTI_PROMPT_TEXT,
        "# Purpose",
        SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_RUST,
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
        rust_variables_checker,
        variables_dict_from_llm_rust_multi_prompt,
        None,
    ),
    (
        S.FN_COND_JSON,
        "# Macros",
        rust_macros_checker,
        macros_dict_from_llm_rust_multi_prompt,
        None,
    ),
    (
        S.FN_COND_JSON,
        "# Traits",
        rust_traits_checker,
        traits_dict_from_llm_rust_multi_prompt,
        None,
    ),
    (
        S.FN_COND_JSON,
        "# Data Structures",
        rust_data_structure_checker,
        data_structure_dict_from_llm_rust_multi_prompt,
        None,
    ),
    (
        S.FN_COND_JSON,
        "# Functions",
        rust_function_checker,
        fn_dict_from_llm_rust_multi_prompt,
        None,
    ),
]
