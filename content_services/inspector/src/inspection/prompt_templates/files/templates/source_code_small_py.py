from utils.lang_specialization.default import default_imports_checker
from utils.lang_specialization.python import (
    SOURCE_CODE_SMALL_PURPOSE_USER_PROMPT,
    SOURCE_CODE_SMALL_SYSTEM_PROMPT_GENERAL_PY,
    data_structure_dict_from_llm_py,
    fn_dict_from_llm_py,
    py_data_structure_checker,
    py_function_checker,
    py_variables_checker,
    variables_dict_from_llm_py,
)
from utils.templates import S


SOURCE_CODE_SMALL_TEMPLATE_PY = [
    (S.SINGLE_PROMPT_TEXT, "# Purpose", SOURCE_CODE_SMALL_SYSTEM_PROMPT_GENERAL_PY, SOURCE_CODE_SMALL_PURPOSE_USER_PROMPT,),
    (S.LLM_COND_JSON,      "\n---\n## Imports and Dependencies", default_imports_checker, lambda _llm, output, _code: output, None,),
    (S.FN_COND_JSON,       "\n---\n## Global Variables", py_variables_checker, variables_dict_from_llm_py, None),
    (S.FN_COND_JSON,       "\n---\n## Data Structures", py_data_structure_checker, data_structure_dict_from_llm_py, None,),
    (S.FN_COND_JSON,       "\n---\n## Functions", py_function_checker, fn_dict_from_llm_py, None,),
]
