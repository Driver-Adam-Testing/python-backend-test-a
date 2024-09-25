from utils.lang_specialization.cpp import (
    DATA_STRUCTURES_NONE_CONTENT,
    FUNCTIONS_NONE_CONTENT,
    SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT,
    SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_CPP,
    VARIABLES_NONE_CONTENT,
    class_dict_from_llm_cpp,
    cpp_class_checker,
    cpp_function_checker,
    cpp_variables_checker,
    fn_dict_from_llm_cpp,
    variables_dict_from_llm_cpp,
)
from utils.lang_specialization.default import (
    IMPORTS_NONE_CONTENT,
    default_imports_checker,
)
from utils.templates import S

SOURCE_CODE_LARGE_TEMPLATE_CPP = [
    (
        S.SINGLE_PROMPT_TEXT,
        "# Purpose",
        SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_CPP,
        SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT,
    ),
    (S.RAW, "# Symbol Documentation"),
    (
        S.LLM_COND_JSON,
        "\n---\n## Imports and Dependencies",
        default_imports_checker,
        lambda _llm, output, _code: output,
        IMPORTS_NONE_CONTENT,
    ),
    (
        S.FN_COND_JSON,
        "\n---\n## Global Variables",
        cpp_variables_checker,
        variables_dict_from_llm_cpp,
        VARIABLES_NONE_CONTENT,
    ),
    (
        S.FN_COND_JSON,
        "\n---\n## Classes and Structs",
        cpp_class_checker,
        class_dict_from_llm_cpp,
        DATA_STRUCTURES_NONE_CONTENT,
    ),
    (
        S.FN_COND_JSON,
        "\n---\n## Free Functions",
        cpp_function_checker,
        fn_dict_from_llm_cpp,
        FUNCTIONS_NONE_CONTENT,
    ),
]
