from utils.lang_specialization.c import (
    DATA_STRUCTURES_FOUND_SYSTEM_PROMPT_JSON,
    DATA_STRUCTURES_FOUND_USER_PROMPT,
    DATA_STRUCTURES_NONE_CONTENT,
    FUNCTIONS_FOUND_SYSTEM_PROMPT_JSON,
    FUNCTIONS_FOUND_USER_PROMPT,
    FUNCTIONS_NONE_CONTENT,
    IMPORTS_SYSTEM_PROMPT_JSON,
    IMPORTS_USER_PROMPT,
    SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_C,
    VARIABLES_FOUND_SYSTEM_PROMPT_JSON,
    VARIABLES_FOUND_USER_PROMPT,
    VARIABLES_NONE_CONTENT,
    c_data_structure_checker,
    c_function_checker,
    c_variables_checker,
)
from utils.lang_specialization.common import (
    DataStructureData,
    DataStructureDict,
    FnData,
    FnDict,
    ImportData,
    VariableData,
    VariableDict,
)
from utils.lang_specialization.default_multi_context import (
    SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT_MULTI_CONTEXT,
    SOURCE_CODE_PURPOSE_FROM_CHUNKS,
    TECHNICAL_CONCEPTS_FROM_CHUNKS,
    TECHNICAL_CONCEPTS_MULTI_CONTEXT,
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


SOURCE_CODE_LARGE_TEMPLATE_C = [
    (S.RAW, "# Overview"),
    (
        S.MULTI_PROMPT_TEXT,
        "## Purpose",
        SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_C,
        SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT_MULTI_CONTEXT,
        SOURCE_CODE_PURPOSE_FROM_CHUNKS,
    ),
    (
        S.MULTI_PROMPT_TEXT,
        "## Technical Summary",
        SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_C,
        TECHNICAL_CONCEPTS_MULTI_CONTEXT,
        TECHNICAL_CONCEPTS_FROM_CHUNKS,
    ),
    (S.RAW, "# Symbol Documentation"),
    # NOTE: for simplicity this only looks at the first file chunk for imports (making assumptions about the structure of the file)
    (
        S.SINGLE_PROMPT_CHUNK_JSON,
        "## Imports and Dependencies",
        IMPORTS_SYSTEM_PROMPT_JSON,
        IMPORTS_USER_PROMPT,
        ImportData.from_llm,
    ),
    (
        S.FN_COND_JSON,
        "## Global Variables",
        c_variables_checker,
        variables_dict_from_llm,
        VARIABLES_NONE_CONTENT,
    ),
    (
        S.FN_COND_JSON,
        "## Data Structures",
        c_data_structure_checker,
        data_structure_dict_from_llm,
        DATA_STRUCTURES_NONE_CONTENT,
    ),
    (
        S.FN_COND_JSON,
        "## Functions",
        c_function_checker,
        fn_dict_from_llm,
        FUNCTIONS_NONE_CONTENT,
    ),
]
