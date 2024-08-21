from utils.lang_specialization.default import (
    IMPORTS_NONE_CONTENT,
)
from utils.lang_specialization.default_multi_context import (
    SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT_MULTI_CONTEXT,
    SOURCE_CODE_PURPOSE_FROM_CHUNKS,
    default_imports_checker_multi_prompt,
)
from utils.lang_specialization.header import (
    DATA_STRUCTURES_NONE_CONTENT,
    FUNCTIONS_NONE_CONTENT,
    SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_C_OR_CPP_HEADER,
    VARIABLES_NONE_CONTENT,
    data_structure_dict_from_llm_header_multi_prompt,
    fn_dict_from_llm_header_multi_prompt,
    header_data_structure_checker,
    header_function_checker,
    header_variables_checker,
    variables_dict_from_llm_header_multi_prompt,
)
from utils.templates import S

SOURCE_CODE_LARGE_MULTI_PROMPT_TEMPLATE_HEADER = [
    (
        S.MULTI_PROMPT_TEXT,
        "# Purpose",
        SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_C_OR_CPP_HEADER,
        SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT_MULTI_CONTEXT,
        SOURCE_CODE_PURPOSE_FROM_CHUNKS,
    ),
    (S.RAW, "# Symbol Documentation"),
    (
        S.MULTI_LLM_COND_JSON,
        "\n---\n## Imports and Dependencies",
        default_imports_checker_multi_prompt,
        lambda _llm, output, _code: output,
        IMPORTS_NONE_CONTENT,
    ),
    (
        S.FN_COND_JSON,
        "\n---\n## Global Variables",
        header_variables_checker,
        variables_dict_from_llm_header_multi_prompt,
        VARIABLES_NONE_CONTENT,
    ),
    (
        S.FN_COND_JSON,
        "\n---\n## Data Structures",
        header_data_structure_checker,
        data_structure_dict_from_llm_header_multi_prompt,
        DATA_STRUCTURES_NONE_CONTENT,
    ),
    (
        S.FN_COND_JSON,
        "\n---\n## Functions",
        header_function_checker,
        fn_dict_from_llm_header_multi_prompt,
        FUNCTIONS_NONE_CONTENT,
    ),
]
