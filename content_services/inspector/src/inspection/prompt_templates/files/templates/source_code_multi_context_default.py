from inspection.prompt_templates.files.templates.source_code_large_default import (
    data_structure_dict_from_llm,
    fn_dict_from_llm,
    variables_dict_from_llm,
)
from utils.lang_specialization.common import (
    DataStructureDict,
    FnDict,
    ImportData,
    VariableDict,
)
from utils.lang_specialization.default import (
    DATA_STRUCTURES_NONE_CONTENT,
    FUNCTIONS_NONE_CONTENT,
    IMPORTS_SYSTEM_PROMPT_JSON,
    IMPORTS_USER_PROMPT,
    SOURCE_CODE_SYSTEM_PROMPT_GENERAL_DEFAULT,
    VARIABLES_NONE_CONTENT,
)
from utils.lang_specialization.default_multi_context import (
    SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT_MULTI_CONTEXT,
    SOURCE_CODE_PURPOSE_FROM_CHUNKS,
    TECHNICAL_CONCEPTS_FROM_CHUNKS,
    TECHNICAL_CONCEPTS_MULTI_CONTEXT,
    default_data_structure_checker_multi_prompt,
    default_function_checker_multi_prompt,
    default_variable_checker_multi_prompt,
)
from utils.models import ChatOpenAI
from utils.templates import S


def variables_dict_from_llm_chunk(
    llm: ChatOpenAI, chunk_indexed_vars_list: list[int, list[str]], code_chunks: str
) -> VariableDict:
    vars_dict = {}
    for idx, vars_list in chunk_indexed_vars_list:
        chunk_vars_dict = variables_dict_from_llm(llm, vars_list, code_chunks[idx])
        vars_dict.update(chunk_vars_dict.data)

    return VariableDict(data=vars_dict)


def data_structure_dict_from_llm_chunk(
    llm: ChatOpenAI, chunk_indexed_ds_lists: list[int, list[str]], code_chunks: str
) -> DataStructureDict:
    ds_dict = {}
    for idx, ds_list in chunk_indexed_ds_lists:
        chunk_ds_dict = data_structure_dict_from_llm(llm, ds_list, code_chunks[idx])
        ds_dict.update(chunk_ds_dict.data)
    return DataStructureDict(data=ds_dict)


def fn_dict_from_llm_chunk(
    llm: ChatOpenAI, chunk_indexed_fn_lists: list[int, list[str]], code_chunks: str
) -> FnDict:
    fn_dict = {}
    for idx, fn_list in chunk_indexed_fn_lists:
        chunk_fn_dict = fn_dict_from_llm(llm, fn_list, code_chunks[idx])
        fn_dict.update(chunk_fn_dict.data)
    return FnDict(data=fn_dict)


SOURCE_CODE_MULTI_CONTEXT_TEMPLATE_DEFAULT = [
    (S.RAW, "# Overview"),
    (
        S.MULTI_PROMPT_TEXT,
        "## Purpose",
        SOURCE_CODE_SYSTEM_PROMPT_GENERAL_DEFAULT,
        SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT_MULTI_CONTEXT,
        SOURCE_CODE_PURPOSE_FROM_CHUNKS,
    ),
    (
        S.MULTI_PROMPT_TEXT,
        "## Technical Summary",
        SOURCE_CODE_SYSTEM_PROMPT_GENERAL_DEFAULT,
        TECHNICAL_CONCEPTS_MULTI_CONTEXT,
        TECHNICAL_CONCEPTS_FROM_CHUNKS,
    ),
    (S.RAW, "# Symbol Documentation"),
    # NOTE: for simplicity this only looks at the first file chunk for imports (making assumptions about the structure of the file)
    (
        S.SINGLE_PROMPT_CHUNK_JSON,
        "\n---\n## Imports and Dependencies",
        IMPORTS_SYSTEM_PROMPT_JSON,
        IMPORTS_USER_PROMPT,
        ImportData.from_llm,
    ),
    (
        S.MULTI_LLM_COND_JSON,
        "\n---\n## Global Variables",
        default_variable_checker_multi_prompt,
        variables_dict_from_llm_chunk,
        VARIABLES_NONE_CONTENT,
    ),
    (
        S.MULTI_LLM_COND_JSON,
        "\n---\n## Data Structures",
        default_data_structure_checker_multi_prompt,
        data_structure_dict_from_llm_chunk,
        DATA_STRUCTURES_NONE_CONTENT,
    ),
    (
        S.MULTI_LLM_COND_JSON,
        "\n---\n## Functions",
        default_function_checker_multi_prompt,
        fn_dict_from_llm_chunk,
        FUNCTIONS_NONE_CONTENT,
    ),
]
