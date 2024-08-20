from pathlib import Path

from utils.codemap_ctags import extract_symbols_w_ctags
from utils.lang_specialization.common import (
    DataStructureData,
    DataStructureDict,
    FnData,
    FnDict,
    VariableData,
    VariableDict,
)
from utils.lang_specialization.cpp import (
    DATA_STRUCTURES_FOUND_SYSTEM_PROMPT_JSON,
    DATA_STRUCTURES_FOUND_USER_PROMPT,
    DATA_STRUCTURES_NONE_CONTENT,
    FUNCTIONS_FOUND_SYSTEM_PROMPT_JSON,
    FUNCTIONS_FOUND_USER_PROMPT,
    FUNCTIONS_NONE_CONTENT,
    SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_CPP,
    VARIABLES_FOUND_SYSTEM_PROMPT_JSON,
    VARIABLES_FOUND_USER_PROMPT,
    VARIABLES_NONE_CONTENT,
    cpp_data_structure_checker,
    cpp_function_checker,
    cpp_variables_checker,
)
from utils.lang_specialization.default import IMPORTS_NONE_CONTENT
from utils.lang_specialization.default_multi_context import (
    SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT_MULTI_CONTEXT,
    SOURCE_CODE_PURPOSE_FROM_CHUNKS,
    TECHNICAL_CONCEPTS_FROM_CHUNKS,
    TECHNICAL_CONCEPTS_MULTI_CONTEXT,
    default_imports_checker_multi_prompt,
)
from utils.models import ChatOpenAI
from utils.templates import S

PADDING_LINES_TOP = 100
PADDING_LINES_BOTTOM = 100


def variables_dict_from_llm(
    llm: ChatOpenAI, vars_list: list[str], code: str, root_rel_path: Path
) -> VariableDict:
    symbols = extract_symbols_w_ctags(root_rel_path=root_rel_path, file_content=code)
    vars_dict = {}
    for v in vars_list:
        for symbol in symbols:
            if symbol["name"] == v:
                start_line = symbol["line"]
                end_line = symbol.get("end", symbol["line"])
                # TODO: programmatically find appropriate padding based on tokens...
                symbol_code = "\n".join(
                    code.splitlines()[
                        start_line - PADDING_LINES_TOP : end_line + PADDING_LINES_BOTTOM
                    ]
                )
                vars_dict[v] = VariableData.from_llm(
                    llm=llm,
                    system_prompt=VARIABLES_FOUND_SYSTEM_PROMPT_JSON,
                    user_prompt=VARIABLES_FOUND_USER_PROMPT,
                    var_name=v,
                    code=symbol_code,
                )
    return VariableDict(data=vars_dict)


def data_structure_dict_from_llm(
    llm: ChatOpenAI, ds_list: list[str], code: str, root_rel_path: Path
) -> DataStructureDict:
    symbols = extract_symbols_w_ctags(root_rel_path=root_rel_path, file_content=code)
    ds_dict = {}
    for ds in ds_list:
        for symbol in symbols:
            if symbol["name"] == ds:
                start_line = symbol["line"]
                end_line = symbol.get("end", symbol["line"])
                # TODO: programmatically find appropriate padding based on tokens...
                symbol_code = "\n".join(
                    code.splitlines()[
                        start_line - PADDING_LINES_TOP : end_line + PADDING_LINES_BOTTOM
                    ]
                )
                ds_dict[ds] = DataStructureData.from_llm(
                    llm=llm,
                    system_prompt=DATA_STRUCTURES_FOUND_SYSTEM_PROMPT_JSON,
                    user_prompt=DATA_STRUCTURES_FOUND_USER_PROMPT,
                    ds_name=ds,
                    code=symbol_code,
                )
                break
    return DataStructureDict(data=ds_dict)


def fn_dict_from_llm(
    llm: ChatOpenAI, fn_list: list[str], code: str, root_rel_path: Path
) -> FnDict:
    symbols = extract_symbols_w_ctags(root_rel_path=root_rel_path, file_content=code)
    fn_dict = {}
    for fn in fn_list:
        for symbol in symbols:
            if symbol["name"] == fn:
                start_line = symbol["line"]
                end_line = symbol.get("end", symbol["line"])
                # TODO: programmatically find appropriate padding based on tokens...
                symbol_code = "\n".join(
                    code.splitlines()[
                        start_line - PADDING_LINES_TOP : end_line + PADDING_LINES_BOTTOM
                    ]
                )
                fn_dict[fn] = FnData.from_llm(
                    llm=llm,
                    system_prompt=FUNCTIONS_FOUND_SYSTEM_PROMPT_JSON,
                    user_prompt=FUNCTIONS_FOUND_USER_PROMPT,
                    fn_name=fn,
                    code=symbol_code,
                )
    return FnDict(data=fn_dict)


SOURCE_CODE_LARGE_MULTI_PROMPT_TEMPLATE_CPP = [
    # (S.RAW,                 "# Overview"),
    (S.MULTI_PROMPT_TEXT,   "# Purpose", SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_CPP, SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT_MULTI_CONTEXT, SOURCE_CODE_PURPOSE_FROM_CHUNKS,),
    # (S.MULTI_PROMPT_TEXT,   "## Technical Summary", SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_CPP, TECHNICAL_CONCEPTS_MULTI_CONTEXT, TECHNICAL_CONCEPTS_FROM_CHUNKS,),
    (S.RAW, "# Symbol Documentation"),
    # NOTE: for simplicity this only looks at the first file chunk for imports (making assumptions about the structure of the file)
    (S.MULTI_LLM_COND_JSON, "\n---\n## Imports and Dependencies", default_imports_checker_multi_prompt, lambda _llm, output, _code: output, IMPORTS_NONE_CONTENT,),
    (S.FN_COND_JSON,        "\n---\n## Global Variables", cpp_variables_checker, variables_dict_from_llm, VARIABLES_NONE_CONTENT,),
    (S.FN_COND_JSON,        "\n---\n## Data Structures", cpp_data_structure_checker, data_structure_dict_from_llm, DATA_STRUCTURES_NONE_CONTENT,),
    (S.FN_COND_JSON,        "\n---\n## Functions", cpp_function_checker, fn_dict_from_llm, FUNCTIONS_NONE_CONTENT,),
]
