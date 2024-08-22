from utils.lang_specialization.default import (
    DATA_STRUCTURES_NONE_CONTENT,
    FUNCTIONS_NONE_CONTENT,
    IMPORTS_NONE_CONTENT,
    SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT,
    SOURCE_CODE_SYSTEM_PROMPT_GENERAL_DEFAULT,
    VARIABLES_NONE_CONTENT,
    data_structure_dict_from_llm_default,
    default_data_structure_checker,
    default_function_checker,
    default_imports_checker,
    default_variable_checker,
    fn_dict_from_llm_default,
    variables_dict_from_llm_default,
)
from utils.templates import S


SOURCE_CODE_LARGE_TEMPLATE_DEFAULT = [
    (S.SINGLE_PROMPT_TEXT, "# Purpose", SOURCE_CODE_SYSTEM_PROMPT_GENERAL_DEFAULT, SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT,),
    (S.RAW,                "# Symbol Documentation"),
    (S.LLM_COND_JSON,      "\n---\n## Imports and Dependencies", default_imports_checker, lambda _llm, output, _code: output, IMPORTS_NONE_CONTENT,),
    (S.LLM_COND_JSON,      "\n---\n## Global Variables", default_variable_checker, variables_dict_from_llm_default, VARIABLES_NONE_CONTENT,),
    (S.LLM_COND_JSON,      "\n---\n## Data Structures", default_data_structure_checker, data_structure_dict_from_llm_default, DATA_STRUCTURES_NONE_CONTENT,),
    (S.LLM_COND_JSON,      "\n---\n## Functions", default_function_checker, fn_dict_from_llm_default, FUNCTIONS_NONE_CONTENT,),
]
