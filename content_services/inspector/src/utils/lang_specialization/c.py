from pathlib import Path

from utils.codemap_ctags import extract_symbols_w_ctags

C_DATA_STRUCTURES = {"enum", "union", "struct", "typedef"}
C_FUNCTIONS = {"function", "prototype"}
C_MACROS = {"macro"}
C_VARIABLES = {"variable", "externvar"}


def c_data_structure_checker(code: str, root_rel_path: Path) -> str | None:
    symbols = extract_symbols_w_ctags(root_rel_path=root_rel_path, file_content=code)
    ds_list = []
    for s in symbols:
        if s["kind"] in C_DATA_STRUCTURES and not s["name"].startswith("__anon"):
            ds_list.append(s["name"])
    if len(ds_list) > 0:
        output = "\nData Structures to document in the code:\n\n"
        for ds in ds_list:
            output += f"- {ds}\n"
    else:
        output = None
    return output


def c_function_checker(code: str, root_rel_path: Path) -> str | None:
    symbols = extract_symbols_w_ctags(root_rel_path=root_rel_path, file_content=code)
    fn_list = [s["name"] for s in symbols if s["kind"] in C_FUNCTIONS]
    if len(fn_list) > 0:
        output = "\nFunctions to document in the code:\n\n"
        for fn in fn_list:
            output += f"- {fn}\n"
    else:
        output = None
    return output


def c_macro_checker(code: str, root_rel_path: Path) -> str | None:
    symbols = extract_symbols_w_ctags(root_rel_path=root_rel_path, file_content=code)
    m_list = [s["name"] for s in symbols if s["kind"] in C_MACROS]
    if len(m_list) > 0:
        output = "\nMacros to document in the code:\n\n"
        for m in m_list:
            output += f"- {m}\n"
    else:
        output = None
    return output


def c_variables_checker(code: str, root_rel_path: Path) -> str | None:
    symbols = extract_symbols_w_ctags(root_rel_path=root_rel_path, file_content=code)
    v_list = [s["name"] for s in symbols if s["kind"] in C_VARIABLES]
    if len(v_list) > 0:
        output = "\nVariables to document in the code:\n\n"
        for v in v_list:
            output += f"- {v}\n"
    else:
        output = None
    return output
