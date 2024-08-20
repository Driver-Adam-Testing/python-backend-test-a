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
from utils.lang_specialization.python import (
    DATA_STRUCTURES_FOUND_SYSTEM_PROMPT_JSON,
    DATA_STRUCTURES_FOUND_USER_PROMPT,
    FUNCTIONS_FOUND_SYSTEM_PROMPT_JSON,
    FUNCTIONS_FOUND_USER_PROMPT,
    VARIABLES_FOUND_SYSTEM_PROMPT_JSON,
    VARIABLES_FOUND_USER_PROMPT,
)
from utils.models import ChatOpenAI

PADDING_LINES_TOP = 100
PADDING_LINES_BOTTOM = 100


def symbols_dict_from_llm(
    llm: ChatOpenAI,
    symbols_list: list[str],
    code: str,
    root_rel_path: Path,
    data_class: VariableData | DataStructureData | FnData,
    system_prompt: str,
    user_prompt: str,
):
    symbols = extract_symbols_w_ctags(root_rel_path=root_rel_path, file_content=code)
    symbols_dict = {}
    for symbol in symbols:
        for s in symbols_list:
            if symbol["name"] == s:
                start_line = symbol["line"]
                end_line = symbol.get("end", symbol["line"])
                symbol_code = "\n".join(
                    code.splitlines()[
                        start_line - PADDING_LINES_TOP : end_line + PADDING_LINES_BOTTOM
                    ]
                )
                symbols_dict[s] = data_class.from_llm(
                    llm,
                    system_prompt,
                    user_prompt,
                    s,
                    symbol_code,
                )
                break
    return symbols_dict


def variables_dict_from_llm(
    llm: ChatOpenAI,
    variables_list: list[str],
    code: str,
    root_rel_path: Path,
):
    symbols_dict = symbols_dict_from_llm(
        llm,
        variables_list,
        code,
        root_rel_path,
        VariableData,
        VARIABLES_FOUND_SYSTEM_PROMPT_JSON,
        VARIABLES_FOUND_USER_PROMPT,
    )
    return VariableDict(data=symbols_dict)


def data_structure_dict_from_llm(
    llm: ChatOpenAI,
    data_structures_list: list[str],
    code: str,
    root_rel_path: Path,
):
    symbols_dict = symbols_dict_from_llm(
        llm,
        data_structures_list,
        code,
        root_rel_path,
        DataStructureData,
        DATA_STRUCTURES_FOUND_SYSTEM_PROMPT_JSON,
        DATA_STRUCTURES_FOUND_USER_PROMPT,
    )
    return DataStructureDict(data=symbols_dict)


def fn_dict_from_llm(
    llm: ChatOpenAI,
    functions_list: list[str],
    code: str,
    root_rel_path: Path,
):
    symbols_dict = symbols_dict_from_llm(
        llm,
        functions_list,
        code,
        root_rel_path,
        FnData,
        FUNCTIONS_FOUND_SYSTEM_PROMPT_JSON,
        FUNCTIONS_FOUND_USER_PROMPT,
    )
    return FnDict(data=symbols_dict)
