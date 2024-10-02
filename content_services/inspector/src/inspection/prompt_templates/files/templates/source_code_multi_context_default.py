from inspection.prompt_templates.files.templates.source_code_large_default import (
    data_structure_dict_from_llm_default,
    fn_dict_from_llm_default,
    variables_dict_from_llm_default,
)
from utils.lang_specialization.common import (
    DataStructureDict,
    FnDict,
    VariableDict,
)
from utils.lang_specialization.default import (
    SOURCE_CODE_SYSTEM_PROMPT_GENERAL_DEFAULT,
)
from utils.lang_specialization.default_multi_context import (
    SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT_MULTI_CONTEXT,
    SOURCE_CODE_PURPOSE_FROM_CHUNKS,
    default_data_structure_checker_multi_prompt,
    default_function_checker_multi_prompt,
    default_imports_checker_multi_prompt,
    default_variable_checker_multi_prompt,
)
from utils.models import ChatOpenAI
from utils.templates import S


def variables_dict_from_llm_chunk(
    llm: ChatOpenAI, chunk_indexed_vars_list: list[int, list[str]], code_chunks: str
) -> VariableDict:
    vars_dict = {}
    for idx, vars_list in chunk_indexed_vars_list:
        chunk_vars_dict = variables_dict_from_llm_default(
            llm, vars_list, code_chunks[idx]
        )
        vars_dict.update(chunk_vars_dict.data)

    return VariableDict(data=vars_dict)


def data_structure_dict_from_llm_chunk(
    llm: ChatOpenAI, chunk_indexed_ds_lists: list[int, list[str]], code_chunks: str
) -> DataStructureDict:
    ds_dict = {}
    for idx, ds_list in chunk_indexed_ds_lists:
        chunk_ds_dict = data_structure_dict_from_llm_default(
            llm, ds_list, code_chunks[idx]
        )
        ds_dict.update(chunk_ds_dict.data)
    return DataStructureDict(data=ds_dict)


def fn_dict_from_llm_chunk(
    llm: ChatOpenAI, chunk_indexed_fn_lists: list[int, list[str]], code_chunks: str
) -> FnDict:
    fn_dict = {}
    for idx, fn_list in chunk_indexed_fn_lists:
        chunk_fn_dict = fn_dict_from_llm_default(llm, fn_list, code_chunks[idx])
        fn_dict.update(chunk_fn_dict.data)
    return FnDict(data=fn_dict)


SOURCE_CODE_MULTI_CONTEXT_TEMPLATE_DEFAULT = [
    (
        S.MULTI_PROMPT_TEXT,
        "# Purpose",
        SOURCE_CODE_SYSTEM_PROMPT_GENERAL_DEFAULT,
        SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT_MULTI_CONTEXT,
        SOURCE_CODE_PURPOSE_FROM_CHUNKS,
    ),
    # NOTE: for simplicity this only looks at the first file chunk for imports (making assumptions about the structure of the file)
    (
        S.MULTI_LLM_COND_JSON,
        "# Imports and Dependencies",
        default_imports_checker_multi_prompt,
        lambda _llm, output, _code: output,
        None,
    ),
    (
        S.MULTI_LLM_COND_JSON,
        "# Global Variables",
        default_variable_checker_multi_prompt,
        variables_dict_from_llm_chunk,
        None,
    ),
    (
        S.MULTI_LLM_COND_JSON,
        "# Data Structures",
        default_data_structure_checker_multi_prompt,
        data_structure_dict_from_llm_chunk,
        None,
    ),
    (
        S.MULTI_LLM_COND_JSON,
        "# Functions",
        default_function_checker_multi_prompt,
        fn_dict_from_llm_chunk,
        None,
    ),
]
