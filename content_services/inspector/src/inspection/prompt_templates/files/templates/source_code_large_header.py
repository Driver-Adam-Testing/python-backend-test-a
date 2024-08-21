from utils.lang_specialization.default import (
    IMPORTS_NONE_CONTENT,
    default_imports_checker,
)
from utils.lang_specialization.header import (
    DATA_STRUCTURES_NONE_CONTENT,
    FUNCTIONS_NONE_CONTENT,
    SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT,
    SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_C_OR_CPP_HEADER,
    VARIABLES_NONE_CONTENT,
    data_structure_dict_from_llm_header,
    fn_dict_from_llm_header,
    header_data_structure_checker,
    header_function_checker,
    header_variables_checker,
    variables_dict_from_llm_header,
)
from utils.templates import S


SOURCE_CODE_LARGE_TEMPLATE_HEADER = [
    (S.SINGLE_PROMPT_TEXT, "# Purpose", SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_C_OR_CPP_HEADER, SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT,),
    (S.RAW,                "# Symbol Documentation"),
    (S.LLM_COND_JSON,      "\n---\n## Imports and Dependencies", default_imports_checker, lambda _llm, output, _code: output, IMPORTS_NONE_CONTENT,),
    (S.FN_COND_JSON,       "\n---\n## Global Variables", header_variables_checker, variables_dict_from_llm_header, VARIABLES_NONE_CONTENT),
    (S.FN_COND_JSON,       "\n---\n## Data Structures", header_data_structure_checker, data_structure_dict_from_llm_header, DATA_STRUCTURES_NONE_CONTENT,),
    (S.FN_COND_JSON,       "\n---\n## Functions", header_function_checker, fn_dict_from_llm_header, FUNCTIONS_NONE_CONTENT,),
]
