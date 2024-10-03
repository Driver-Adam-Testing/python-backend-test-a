from utils.lang_specialization.assembly import (
    SOURCE_CODE_SMALL_PURPOSE_USER_PROMPT,
    SOURCE_CODE_SYSTEM_PROMPT_GENERAL_DEFAULT,
    assembly_data_structure_checker,
    assembly_function_checker,
    assembly_imports_checker,
    assembly_macro_checker,
    assembly_variable_checker,
    data_structure_dict_from_llm_assembly,
    fn_dict_from_llm_assembly,
    macro_dict_from_llm_assembly,
    variables_dict_from_llm_assembly,
)
from utils.templates import S

SOURCE_CODE_SMALL_TEMPLATE_ASSEMBLY = [
    (
        S.SINGLE_PROMPT_TEXT,
        "# Purpose",
        SOURCE_CODE_SYSTEM_PROMPT_GENERAL_DEFAULT,
        SOURCE_CODE_SMALL_PURPOSE_USER_PROMPT,
    ),
    (
        S.LLM_COND_JSON,
        "# Imports and Dependencies",
        assembly_imports_checker,
        lambda _llm, output, _code: output,
        None,
    ),
    (
        S.LLM_COND_JSON,
        "# Global Variables",
        assembly_variable_checker,
        variables_dict_from_llm_assembly,
        None,
    ),
    (
        S.LLM_COND_JSON,
        "# Data Structures",
        assembly_data_structure_checker,
        data_structure_dict_from_llm_assembly,
        None,
    ),
    (
        S.LLM_COND_JSON,
        "# Subroutines",
        assembly_function_checker,
        fn_dict_from_llm_assembly,
        None,
    ),
    (
        S.LLM_COND_JSON,
        "# Macros",
        assembly_macro_checker,
        macro_dict_from_llm_assembly,
        None,
    ),
]
