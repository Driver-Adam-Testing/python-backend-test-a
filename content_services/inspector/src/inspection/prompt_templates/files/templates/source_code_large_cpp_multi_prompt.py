from utils.lang_specialization.cpp import (
    SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_CPP,
    cpp_data_structure_checker,
    cpp_function_checker,
    cpp_variables_checker,
    data_structure_dict_from_llm_cpp_multi_prompt,
    fn_dict_from_llm_cpp_multi_prompt,
    variables_dict_from_llm_cpp_multi_prompt,
)
from utils.lang_specialization.default_multi_context import (
    SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT_MULTI_CONTEXT,
    SOURCE_CODE_PURPOSE_FROM_CHUNKS,
    default_imports_checker_multi_prompt,
)
from utils.templates import S

SOURCE_CODE_LARGE_MULTI_PROMPT_TEMPLATE_CPP = [
    (
        S.MULTI_PROMPT_TEXT,
        "# Purpose",
        SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_CPP,
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
        cpp_variables_checker,
        variables_dict_from_llm_cpp_multi_prompt,
        None,
    ),
    (
        S.FN_COND_JSON,
        "# Data Structures",
        cpp_data_structure_checker,
        data_structure_dict_from_llm_cpp_multi_prompt,
        None,
    ),
    (
        S.FN_COND_JSON,
        "# Functions",
        cpp_function_checker,
        fn_dict_from_llm_cpp_multi_prompt,
        None,
    ),
]
