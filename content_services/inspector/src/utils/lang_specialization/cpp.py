from pathlib import Path

from utils.codemap_ctags import extract_symbols_w_ctags

CPP_DATA_STRUCTURES = {"enum", "union", "struct", "class", "typedef"}
CPP_FUNCTIONS = {"function", "prototype"}
CPP_MACROS = {"macro"}
CPP_VARIABLES = {"variable", "externvar"}


SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_CPP = """
You are an expert C++ programmer and a software engineering documentation expert. You write detailed documentation to explain code written in C++.

You are skilled at explaining technical details as well as recognize and articulate the key conceptual components and purpose of software.
"""

SOURCE_CODE_SMALL_SYSTEM_PROMPT_GENERAL_CPP = """
You are an expert C++ programmer and a software engineering documentation expert. You write detailed documentation to explain code written in C++.

You are skilled at explaining technical details as well as recognize and articulate the key conceptual components and purpose of software.

You specialize in effectively describing small and short source code files. Your goal is to be terse and clear, since the source code you are describing is small and simple.
"""

SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT = """
You will be given the content of a source code file. In a single paragraph of 3 to 5 sentences, explain the purpose of the file. Consider questions such as the following when providing your output:

- Does this code provide narrow or broad functionality?
- Is this code a collection of many different components? If so, what is the common theme or purpose?
- What kind of code is this? For example, is this code clearly an executable (e.g., main.cpp), a C++ header file, a C++ file or library intended to be imported elsewhere?
- Does it define public APIs or external interfaces?
"""

SOURCE_CODE_SMALL_PURPOSE_USER_PROMPT = """
In a single paragraph of 3 to 5 sentences, explain the purpose of the code provided below. Consider questions such as the following when providing your output:

- Does this code provide narrow or broad functionality?
- What kind of code is this? For example, is this code clearly an executable (e.g., main.cpp), a C++ header file, a C++ file or library intended to be imported elsewhere?
"""

TECHNICAL_CONCEPTS = """
You will be given the content of a source code file. In a single paragraph of 3 to 5 sentences, describe the important technical features and their interactions in the file.

In writing your description, write about about the conceptual use cases, applications, logic, and component interactions instead of focusing on particular functions, variables, etc.
"""

IMPORTS_SYSTEM_PROMPT_JSON = """
Summarize the header files and imports used in the code provided below.

**Always respond using exactly the following JSON schema**:
{
    "data": [
        {"name": <import1_name>, "content": <1 sentence description of the first import or header>},
        {"name": <import2_name>, "content": <1 sentence description of the second import or header>},
        ...
    ]
}
"""

IMPORTS_USER_PROMPT = """
Summarize the header files and imports used in the code provided below.

- If there are no header files or imports, just return an empty list.
- If it is completely clear what a header file or import is for, briefly describe it. Do not speculate -- if it is not completely clear what a header file provides just identify it and leave the value associated with `content` empty.
"""

DATA_STRUCTURES_FOUND_SYSTEM_PROMPT_JSON = """
You are an expert C++ programmer and a software engineering documentation expert. You write detailed documentation to explain code written in C++.

You focus on writing technical documentation for data structures such as structs, enums, and classes in C++. You are skilled at explaining technical details as well as recognizing and articulating the key conceptual components and purpose of software.

You will be given the name of a data structure to document and the source code where the data structure is defined.

Your job is to describe the data structure. **Always respond using exactly the following JSON schema**:
{
    "type": <type of the data structure>,
    "members": [
        {"name": <member_name1>, "content": <Terse 1 sentence description of the first member or field>},
        {"name": <member_name2>, "content": <Terse 1 sentence description of the second member or field>},
        ...
    ],
    "description": <one paragraph description of the data structure>,
}

Return JSON according to the schema above. Do not use the format ```json ... ```, just return the JSON data.
"""

DATA_STRUCTURES_FOUND_USER_PROMPT = """
Summarize the data structure in the code provided below.

- A data structure is custom or compound type in a given programming language, such as structs, classes, or enums. Functions, methods, and variables are not data structures.
- When describing an important data structure, provide detail that matches the complexity of the data structure. Large and complex data structures should get longer explanations, while small ones a single sentence.
"""

DATA_STRUCTURES_NONE_CONTENT = "No custom data structures defined in this file."


FUNCTIONS_FOUND_SYSTEM_PROMPT_JSON = """
You are an expert C++ programmer and a software engineering documentation expert. You write detailed documentation to explain code written in C++.

You focus on writing technical documentation for functions and class methods. You are skilled at explaining technical details as well as recognizing and articulating the key conceptual components and purpose of software.

You will be given the name of a function to document and the source code where the function is defined.

Your job is to describe the function. **Always respond using exactly the following JSON schema**:
{
    "single_sentence": <terse single sentence description of the function>,
    "inputs": [
        {"name": <input_arg1>, "content": <description of input argument 1>},
        {"name": <input_arg2>, "content": <description of input argument 2>},
        ...
    ],
    "control_flow": [
        <bullet point 1 for description of control flow>,
        <bullet point 2 for description of control flow>,
        ...
    ],
    "output": <description of output>
}

Return JSON according to the schema above. Do not use the format ```json ... ```, just return the JSON data.
"""

FUNCTIONS_FOUND_USER_PROMPT = """
Summarize the function or method in the code provided below. Describe the inputs, control flow and logic, and output.

- When describing a function, provide detail that matches the complexity of the function body. Large and complex functions should get longer explanations, while small ones much less.
"""

FUNCTIONS_NONE_CONTENT = "No functions or function prototypes defined in this file."

VARIABLES_FOUND_SYSTEM_PROMPT_JSON = """
You are an expert C++ programmer and a software engineering documentation expert. You write detailed documentation to explain code written in C++.

You focus on writing technical documentation for variables. You are skilled at explaining technical details as well as recognizing and articulating the key conceptual components and purpose of software.

You will be given the name of a variable to document and the source code where the data structure is defined.

Your job is to describe the data structure. **Always respond using exactly the following JSON schema**:
{
    "type": <type of the variable>,
    "description": <1 to 3 sentence description of the variable>,
    "use": <Terse 1 sentence description of how this variable is used>,
}

Return JSON according to the schema above. Do not use the format ```json ... ```, just return the JSON data.
"""

VARIABLES_FOUND_USER_PROMPT = """
Summarize the variable in the code provided below.

- A global variable is declared at the top level scope. Local variables declared and used inside of functions are not global variables. You will be describing a global variable.
- When describing a variable, provide detail that matches the complexity of the variable. Large and complex global variables (e.g., containing large struct instances) should get longer explanations, while small ones (e.g., one line definitions) much less.
"""

VARIABLES_NONE_CONTENT = "No global variables defined in this file."


def cpp_data_structure_checker(
    code: str, root_rel_path: Path, structured_output: bool = True
) -> list[str] | str | None:
    symbols = extract_symbols_w_ctags(root_rel_path=root_rel_path, file_content=code)
    ds_list = []
    for s in symbols:
        if s["kind"] in CPP_DATA_STRUCTURES and not s["name"].startswith("__anon"):
            ds_list.append(s["name"])
    if len(ds_list) > 0:
        if structured_output:
            output = ds_list
        else:
            output = "\nData Structures to document in the code:\n\n"
            for ds in ds_list:
                output += f"- {ds}\n"
    else:
        output = None
    return output


def cpp_function_checker(
    code: str, root_rel_path: Path, structured_output: bool = True
) -> list[str] | str | None:
    symbols = extract_symbols_w_ctags(root_rel_path=root_rel_path, file_content=code)
    fn_list = [s["name"] for s in symbols if s["kind"] in CPP_FUNCTIONS]
    if len(fn_list) > 0:
        if structured_output:
            output = fn_list
        else:
            output = "\nFunctions to document in the code:\n\n"
            for fn in fn_list:
                output += f"- {fn}\n"
    else:
        output = None
    return output


def cpp_macro_checker(
    code: str, root_rel_path: Path, structured_output: bool = True
) -> list[str] | str | None:
    symbols = extract_symbols_w_ctags(root_rel_path=root_rel_path, file_content=code)
    m_list = [s["name"] for s in symbols if s["kind"] in CPP_MACROS]
    if len(m_list) > 0:
        if structured_output:
            output = m_list
        else:
            output = "\nMacros to document in the code:\n\n"
            for m in m_list:
                output += f"- {m}\n"
    else:
        output = None
    return output


def cpp_variables_checker(
    code: str, root_rel_path: Path, structured_output: bool = True
) -> list[str] | str | None:
    symbols = extract_symbols_w_ctags(root_rel_path=root_rel_path, file_content=code)
    v_list = [s["name"] for s in symbols if s["kind"] in CPP_VARIABLES]
    if len(v_list) > 0:
        if structured_output:
            output = v_list
        else:
            output = "\nVariables to document in the code:\n\n"
            for v in v_list:
                output += f"- {v}\n"
    else:
        output = None
    return output


def cpp_namespace_checker(
    code: str, root_rel_path: Path, structured_output: bool = True
) -> list[str] | str | None:
    symbols = extract_symbols_w_ctags(root_rel_path=root_rel_path, file_content=code)
    ns_list = [s["name"] for s in symbols if s["kind"] == "namespace"]
    if len(ns_list) > 0:
        if structured_output:
            output = ns_list
        else:
            output = "\nNamespaces to document in the code:\n\n"
            for ns in ns_list:
                output += f"- {ns}\n"
    else:
        output = None
    return output
