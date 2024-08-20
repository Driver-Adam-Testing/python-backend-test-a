from inspection.prompt_templates.files.templates.source_code_multi_prompt_common import (
    data_structure_dict_from_llm,
    fn_dict_from_llm,
    variables_dict_from_llm,
)
from utils.lang_specialization.cpp import (
    DATA_STRUCTURES_NONE_CONTENT,
    FUNCTIONS_NONE_CONTENT,
    SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_CPP,
    VARIABLES_NONE_CONTENT,
    cpp_data_structure_checker,
    cpp_function_checker,
    cpp_variables_checker,
)
from utils.lang_specialization.default import IMPORTS_NONE_CONTENT
from utils.lang_specialization.default_multi_context import (
    SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT_MULTI_CONTEXT,
    SOURCE_CODE_PURPOSE_FROM_CHUNKS,
    default_imports_checker_multi_prompt,
)
from utils.templates import S

SOURCE_CODE_LARGE_MULTI_PROMPT_TEMPLATE_CPP = [
    # (S.RAW,                 "# Overview"),
    (
        S.MULTI_PROMPT_TEXT,
        "# Purpose",
        SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_CPP,
        SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT_MULTI_CONTEXT,
        SOURCE_CODE_PURPOSE_FROM_CHUNKS,
    ),
    # (S.MULTI_PROMPT_TEXT,   "## Technical Summary", SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_CPP, TECHNICAL_CONCEPTS_MULTI_CONTEXT, TECHNICAL_CONCEPTS_FROM_CHUNKS,),
    (S.RAW, "# Symbol Documentation"),
    # NOTE: for simplicity this only looks at the first file chunk for imports (making assumptions about the structure of the file)
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
        cpp_variables_checker,
        variables_dict_from_llm,
        VARIABLES_NONE_CONTENT,
    ),
    (
        S.FN_COND_JSON,
        "\n---\n## Data Structures",
        cpp_data_structure_checker,
        data_structure_dict_from_llm,
        DATA_STRUCTURES_NONE_CONTENT,
    ),
    (
        S.FN_COND_JSON,
        "\n---\n## Functions",
        cpp_function_checker,
        fn_dict_from_llm,
        FUNCTIONS_NONE_CONTENT,
    ),
]
