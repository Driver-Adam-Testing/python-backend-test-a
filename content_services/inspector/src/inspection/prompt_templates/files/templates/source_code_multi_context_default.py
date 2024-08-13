from utils.lang_specialization.default_multi_context import (
    IMPORTS_USER_PROMPT_MULTI_CONTEXT,
    SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT_MULTI_CONTEXT,
    SOURCE_CODE_PURPOSE_FROM_CHUNKS,
    SOURCE_CODE_SYSTEM_PROMPT_GENERAL_DEFAULT_MULTI_CONTEXT,
    TECHNICAL_CONCEPTS_FROM_CHUNKS,
    TECHNICAL_CONCEPTS_MULTI_CONTEXT,
)
from utils.templates import S

# def variables_dict_from_llm_chunk(
#     llm: ChatOpenAI, vars_list: list[str], code_chunks: str
# ) -> VariableDict:
#     vars_dict = {
#         v: VariableData.from_llm(
#             llm=llm,
#             system_prompt=VARIABLES_FOUND_SYSTEM_PROMPT_JSON_MULTI_CONTEXT,
#             user_prompt=VARIABLES_FOUND_USER_PROMPT_MULTI_CONTEXT,
#             var_name=v,
#             code=code_chunk,
#         )
#         for v in vars_list
#     }
#     return VariableDict(data=vars_dict)
#
#
# def data_structure_dict_from_llm_chunk(
#     llm: ChatOpenAI, ds_list: list[str], code_chunks: str
# ) -> DataStructureDict:
#     ds_dict = {
#         ds: DataStructureData.from_llm(
#             llm=llm,
#             system_prompt=DATA_STRUCTURES_FOUND_SYSTEM_PROMPT_JSON_MULTI_CONTEXT,
#             user_prompt=DATA_STRUCTURES_FOUND_USER_PROMPT_MULTI_CONTEXT,
#             ds_name=ds,
#             code=code_chunk,
#         )
#         for ds in ds_list
#     }
#     return DataStructureDict(data=ds_dict)
#
#
# def fn_dict_from_llm_chunk(llm: ChatOpenAI, fn_list: list[str], code_chunks: str) -> FnDict:
#     fn_dict = {
#         fn: FnData.from_llm(
#             llm=llm,
#             system_prompt=FUNCTIONS_FOUND_SYSTEM_PROMPT_JSON_MULTI_CONTEXT,
#             user_prompt=FUNCTIONS_FOUND_USER_PROMPT_MULTI_CONTEXT,
#             fn_name=fn,
#             code=code_chunk,
#         )
#         for fn in fn_list
#     }
#     return FnDict(data=fn_dict)


SOURCE_CODE_MULTI_CONTEXT_TEMPLATE_DEFAULT = [
    (S.RAW, "# Overview"),
    (
        S.MULTI_PROMPT_TEXT,
        "## Purpose",
        SOURCE_CODE_SYSTEM_PROMPT_GENERAL_DEFAULT_MULTI_CONTEXT,
        SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT_MULTI_CONTEXT,
        SOURCE_CODE_PURPOSE_FROM_CHUNKS,
    ),
    (
        S.MULTI_PROMPT_TEXT,
        "## Technical Summary",
        SOURCE_CODE_SYSTEM_PROMPT_GENERAL_DEFAULT_MULTI_CONTEXT,
        TECHNICAL_CONCEPTS_MULTI_CONTEXT,
        TECHNICAL_CONCEPTS_FROM_CHUNKS,
    ),
    (S.RAW, "# Symbol Documentation"),
    (
        S.SINGLE_PROMPT_CHUNK,
        "## Imports and Dependencies",
        SOURCE_CODE_SYSTEM_PROMPT_GENERAL_DEFAULT_MULTI_CONTEXT,
        IMPORTS_USER_PROMPT_MULTI_CONTEXT,
    ),
    # (S.LLM_COND_JSON, "## Global Variables", default_variable_checker_multi_prompt, variables_dict_from_llm_chunk, VARIABLES_NONE_CONTENT_MULTI_CONTEXT,),
    # (S.LLM_COND_JSON, "## Data Structures", default_data_structure_checker_multi_prompt, data_structure_dict_from_llm_chunk, DATA_STRUCTURES_NONE_CONTENT_MULTI_CONTEXT,),
    # (S.LLM_COND_JSON, "## Functions", default_function_checker_multi_prompt, fn_dict_from_llm_chunk, FUNCTIONS_NONE_CONTENT_MULTI_CONTEXT,),
]
