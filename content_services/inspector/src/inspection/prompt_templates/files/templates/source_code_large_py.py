from utils.lang_specialization.common import (
    DataStructureData,
    DataStructureDict,
    FnData,
    FnDict,
    VariableData,
    VariableDict,
)
from utils.lang_specialization.default import (
    IMPORTS_NONE_CONTENT,
    default_imports_checker,
)
from utils.lang_specialization.python import (
    DATA_STRUCTURES_FOUND_SYSTEM_PROMPT_JSON,
    DATA_STRUCTURES_FOUND_USER_PROMPT,
    DATA_STRUCTURES_NONE_CONTENT,
    FUNCTIONS_FOUND_SYSTEM_PROMPT_JSON,
    FUNCTIONS_FOUND_USER_PROMPT,
    FUNCTIONS_NONE_CONTENT,
    SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT,
    SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_PY,
    TECHNICAL_CONCEPTS,
    VARIABLES_FOUND_SYSTEM_PROMPT_JSON,
    VARIABLES_FOUND_USER_PROMPT,
    VARIABLES_NONE_CONTENT,
    py_data_structure_checker,
    py_function_checker,
    py_variables_checker,
)
from utils.models import ChatOpenAI
from utils.templates import S


def variables_dict_from_llm(
    llm: ChatOpenAI, vars_list: list[str], code: str
) -> VariableDict:
    vars_dict = {
        v: VariableData.from_llm(
            llm=llm,
            system_prompt=VARIABLES_FOUND_SYSTEM_PROMPT_JSON,
            user_prompt=VARIABLES_FOUND_USER_PROMPT,
            var_name=v,
            code=code,
        )
        for v in vars_list
    }
    return VariableDict(data=vars_dict)


def data_structure_dict_from_llm(
    llm: ChatOpenAI, ds_list: list[str], code: str
) -> DataStructureDict:
    ds_dict = {
        ds: DataStructureData.from_llm(
            llm=llm,
            system_prompt=DATA_STRUCTURES_FOUND_SYSTEM_PROMPT_JSON,
            user_prompt=DATA_STRUCTURES_FOUND_USER_PROMPT,
            ds_name=ds,
            code=code,
        )
        for ds in ds_list
    }
    return DataStructureDict(data=ds_dict)


def fn_dict_from_llm(llm: ChatOpenAI, fn_list: list[str], code: str) -> FnDict:
    fn_dict = {
        fn: FnData.from_llm(
            llm=llm,
            system_prompt=FUNCTIONS_FOUND_SYSTEM_PROMPT_JSON,
            user_prompt=FUNCTIONS_FOUND_USER_PROMPT,
            fn_name=fn,
            code=code,
        )
        for fn in fn_list
    }
    return FnDict(data=fn_dict)


SOURCE_CODE_LARGE_TEMPLATE_PY = [
    # (S.RAW,                "# Overview"),
    (S.SINGLE_PROMPT_TEXT, "# Purpose", SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_PY, SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT,),
    # (S.SINGLE_PROMPT_TEXT, "## Technical Summary", SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_PY, TECHNICAL_CONCEPTS,),
    (S.RAW,                "# Symbol Documentation"),
    (S.LLM_COND_JSON,      "\n---\n## Imports and Dependencies", default_imports_checker, lambda _llm, output, _code: output, IMPORTS_NONE_CONTENT,),
    (S.FN_COND_JSON,       "\n---\n## Global Variables", py_variables_checker, variables_dict_from_llm, VARIABLES_NONE_CONTENT),
    (S.FN_COND_JSON,       "\n---\n## Data Structures", py_data_structure_checker, data_structure_dict_from_llm, DATA_STRUCTURES_NONE_CONTENT,),
    (S.FN_COND_JSON,       "\n---\n## Functions", py_function_checker, fn_dict_from_llm, FUNCTIONS_NONE_CONTENT,),
]
