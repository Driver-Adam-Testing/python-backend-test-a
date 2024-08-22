from utils.lang_specialization.c import (
    DATA_STRUCTURES_NONE_CONTENT,
    FUNCTIONS_NONE_CONTENT,
    SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT,
    SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_C,
    VARIABLES_NONE_CONTENT,
    c_data_structure_checker,
    c_function_checker,
    c_variables_checker,
    data_structure_dict_from_llm_c,
    fn_dict_from_llm_c,
    variables_dict_from_llm_c,
)
from utils.lang_specialization.default import (
    IMPORTS_NONE_CONTENT,
    default_imports_checker,
)
from utils.templates import S


SOURCE_CODE_LARGE_TEMPLATE_C = [
    (S.SINGLE_PROMPT_TEXT, "# Purpose", SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_C, SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT,),
    (S.RAW,                "# Symbol Documentation"),
    (S.LLM_COND_JSON,      "\n---\n## Imports and Dependencies", default_imports_checker, lambda _llm, output, _code: output, IMPORTS_NONE_CONTENT,),
    (S.FN_COND_JSON,       "\n---\n## Global Variables", c_variables_checker, variables_dict_from_llm_c, VARIABLES_NONE_CONTENT),
    (S.FN_COND_JSON,       "\n---\n## Data Structures", c_data_structure_checker, data_structure_dict_from_llm_c, DATA_STRUCTURES_NONE_CONTENT,),
    (S.FN_COND_JSON,       "\n---\n## Functions", c_function_checker, fn_dict_from_llm_c, FUNCTIONS_NONE_CONTENT,),
]
