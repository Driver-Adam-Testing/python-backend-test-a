from functools import partial
from pathlib import Path
from typing import Self

from utils.codemap_ctags import extract_symbols_w_ctags

# from .common import (
#     class_dict_from_llm,
#     classes_dict_from_llm_multi_prompt,
#     data_structure_dict_from_llm,
#     data_structure_dict_from_llm_multi_prompt,
#     fn_dict_from_llm,
#     fn_dict_from_llm_multi_prompt,
#     variables_dict_from_llm,
#     variables_dict_from_llm_multi_prompt,
# )
from .common_v2 import (
    ClassData,
    ClassDict,
    FnData,
    FnDict,
    ParserKind,
    RawSymbolCollection,
    RawSymbolData,
    SymbolKind,
    VariableData,
    VariableDict,
    code_requires_multi_prompt,
    create_to_be_documented_raw_symbol_via_ctags,
    create_undocumented_raw_symbol_via_ctags,
)

CPP_DATA_STRUCTURES = {"class", "struct", "enum", "union", "typedef"}
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
You will be given the content of a source code file. In 1 or 2 paragraphs, explain the purpose of the file.

When writing your paragraphs, do not use speculative language.

When writing your paragraphs, consider questions like the following. You do not need to explicitly state these ideas, they are just given as examples of the kind of information to provide:

- Does this code provide narrow or broad functionality?
- What are the most important technical components?
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
    "inherits_from": [<list of parent classes or structs>],
}

Return JSON according to the schema above. Do not use the format ```json ... ```, just return the JSON data.
"""

DATA_STRUCTURES_FOUND_USER_PROMPT = """
Summarize the data structure in the code provided below.

- A data structure is custom or compound type in a given programming language, such as structs, classes, or enums. Functions, methods, and variables are not data structures.
- When describing an important data structure, provide detail that matches the complexity of the data structure. Large and complex data structures should get longer explanations, while small ones a single sentence.

Data structure to document:
"""

DATA_STRUCTURES_NONE_CONTENT = "\n---\nNo custom data structures defined in this file."


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

Function to document:
"""

FUNCTIONS_NONE_CONTENT = (
    "\n---\nNo functions or function prototypes defined in this file."
)

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

Variable to document:
"""

VARIABLES_NONE_CONTENT = "\n---\nNo global variables defined in this file."


class CppClassRawSymbolCollection(RawSymbolCollection):
    data: dict[str, RawSymbolData]

    @classmethod
    def from_ctags(cls, code: str, root_rel_path: Path) -> Self | None:
        is_multi_prompt = code_requires_multi_prompt(code)

        symbols = extract_symbols_w_ctags(
            root_rel_path=root_rel_path, file_content=code
        )

        global_method_counts = {}
        class_raw_symbol_data = {}
        for s in symbols:
            if s["kind"] in CPP_FUNCTIONS and not s["name"].startswith("__anon"):
                global_method_counts[s["name"]] = (
                    global_method_counts.get(s["name"], 0) + 1
                )
            if s["kind"] in CPP_DATA_STRUCTURES and not s["name"].startswith("__anon"):
                class_raw_symbol_data[s["name"]] = (
                    create_to_be_documented_raw_symbol_via_ctags(
                        ctags_symbol=s,
                        root_rel_path=root_rel_path,
                        code=code,
                        symbol_kind=SymbolKind.DATA_STRUCTURE,
                        ir_kind=ClassData,
                        scope_relation=None,
                        delimiter="::",
                        is_multi_prompt=is_multi_prompt,
                    )
                )

        for s in symbols:
            if (
                (s.get("scope"))
                and not s["name"].startswith("__anon")
                and (s["kind"] in CPP_FUNCTIONS)
                and s["scopeKind"] in CPP_DATA_STRUCTURES
            ):
                if s["scope"].split("::")[-1] not in class_raw_symbol_data:
                    # Case where class is defined elsewhere (e.g. header), but methods for the class are defined in file
                    class_raw_symbol_data[s["scope"].split("::")[-1]] = RawSymbolData(
                        parser_kind=ParserKind.UCTAGS,
                        symbol_kind=SymbolKind.DATA_STRUCTURE,
                        ir_kind=ClassData,
                        name=s["scope"].split("::")[-1],
                        path=root_rel_path,
                        scope=None,
                        scope_relation=None,
                        children=[],
                        start_line=s["line"],
                        end_line=s["end"],
                        text=None,
                        delimiter="::",
                    )

                is_overloaded = global_method_counts[s["name"]] > 1
                class_raw_symbol_data[s["scope"].split("::")[-1]].children.append(
                    create_to_be_documented_raw_symbol_via_ctags(
                        ctags_symbol=s,
                        root_rel_path=root_rel_path,
                        code=code,
                        symbol_kind=SymbolKind.CALLABLE,
                        ir_kind=FnData,
                        scope_relation="methods",
                        delimiter="::",
                        is_multi_prompt=is_multi_prompt,
                        is_overloaded=is_overloaded,
                    )
                )
            elif (
                (s.get("scope"))
                and not s["name"].startswith("__anon")
                and (s["kind"] in CPP_DATA_STRUCTURES)
                and (s["scopeKind"] in CPP_DATA_STRUCTURES)
            ):
                if s["scope"].split("::")[-1] in class_raw_symbol_data:
                    class_raw_symbol_data[s["scope"].split("::")[-1]].children.append(
                        create_undocumented_raw_symbol_via_ctags(
                            ctags_symbol=s,
                            root_rel_path=root_rel_path,
                            symbol_kind=SymbolKind.DATA_STRUCTURE,
                            scope_relation="nested_classes",
                            delimiter="::",
                        )
                    )
        output = (
            None if len(class_raw_symbol_data) == 0 else cls(data=class_raw_symbol_data)
        )
        return output

    @classmethod
    def from_ts(cls, code: str, root_rel_path: str) -> Self:
        pass

    def to_dict(self) -> dict[str, RawSymbolData]:
        return self.data


class CppFreeFnRawSymbolCollection(RawSymbolCollection):
    data: dict[str, list[RawSymbolData]]

    @classmethod
    def from_ctags(cls, code: str, root_rel_path: str) -> Self:
        is_multi_prompt = code_requires_multi_prompt(code)

        symbols = extract_symbols_w_ctags(
            root_rel_path=root_rel_path, file_content=code
        )

        all_fn_names = [
            s["name"]
            for s in symbols
            if s["kind"] in CPP_FUNCTIONS and not s["name"].startswith("__anon")
        ]

        fn_raw_symbol_data = {}
        for s in symbols:
            if s["kind"] in CPP_FUNCTIONS and not s["name"].startswith("__anon"):
                contained_in_class = False
                if (s.get("scope")) and (s.get("scopeKind") in CPP_DATA_STRUCTURES):
                    contained_in_class = True

                fn_name = (
                    s["name"]
                    if s.get("scopeKind") not in CPP_DATA_STRUCTURES
                    else s["scope"].split("::")[-1] + "::" + s["name"]
                )
                s["name"] = fn_name
                if not contained_in_class and all_fn_names.count(s["name"]) == 1:
                    if fn_name not in fn_raw_symbol_data:
                        fn_raw_symbol_data[fn_name] = []
                    fn_raw_symbol_data[fn_name].append(
                        create_to_be_documented_raw_symbol_via_ctags(
                            ctags_symbol=s,
                            root_rel_path=root_rel_path,
                            code=code,
                            symbol_kind=SymbolKind.CALLABLE,
                            ir_kind=FnData,
                            scope_relation=None,
                            delimiter="::",
                            is_multi_prompt=is_multi_prompt,
                            is_overloaded=False,
                        )
                    )

                elif not contained_in_class and all_fn_names.count(s["name"]) > 1:
                    if fn_name not in fn_raw_symbol_data:
                        fn_raw_symbol_data[fn_name] = []
                    fn_raw_symbol_data[fn_name].append(
                        create_to_be_documented_raw_symbol_via_ctags(
                            ctags_symbol=s,
                            root_rel_path=root_rel_path,
                            code=code,
                            symbol_kind=SymbolKind.CALLABLE,
                            ir_kind=FnData,
                            scope_relation=None,
                            delimiter="::",
                            is_multi_prompt=is_multi_prompt,
                            is_overloaded=True,
                        )
                    )
        output = None if len(fn_raw_symbol_data) == 0 else cls(data=fn_raw_symbol_data)
        return output

    @classmethod
    def from_ts(cls, code: str, root_rel_path: str) -> Self:
        pass

    def to_dict(self) -> dict[str, RawSymbolData]:
        return self.data


class CppVariableRawSymbolCollection(RawSymbolCollection):
    data: dict[str, RawSymbolData]

    @classmethod
    def from_ctags(cls, code: str, root_rel_path: Path) -> Self | None:
        is_multi_prompt = code_requires_multi_prompt(code)

        symbols = extract_symbols_w_ctags(
            root_rel_path=root_rel_path, file_content=code
        )

        variable_raw_symbol_data = {}
        for s in symbols:
            if s["kind"] in CPP_VARIABLES and not s["name"].startswith("__anon"):
                variable_raw_symbol_data[s["name"]] = (
                    create_to_be_documented_raw_symbol_via_ctags(
                        ctags_symbol=s,
                        root_rel_path=root_rel_path,
                        code=code,
                        symbol_kind=SymbolKind.VARIABLE,
                        ir_kind=VariableData,
                        scope_relation=None,
                        delimiter="::",
                        is_multi_prompt=is_multi_prompt,
                        use_padding=True,
                    )
                )

        output = (
            None
            if len(variable_raw_symbol_data) == 0
            else cls(data=variable_raw_symbol_data)
        )
        return output

    @classmethod
    def from_ts(cls, code: str, root_rel_path: str) -> Self:
        pass

    def to_dict(self) -> dict[str, RawSymbolData]:
        return self.data


class_dict_from_llm_cpp = partial(
    ClassDict.dict_from_llm,
    {
        "base_data": DATA_STRUCTURES_FOUND_SYSTEM_PROMPT_JSON,
        "methods": FUNCTIONS_FOUND_SYSTEM_PROMPT_JSON,
    },
    {
        "base_data": DATA_STRUCTURES_FOUND_USER_PROMPT,
        "methods": FUNCTIONS_FOUND_USER_PROMPT,
    },
    ClassData,
)

fn_dict_from_llm_cpp = partial(
    FnDict.dict_from_llm,
    FUNCTIONS_FOUND_SYSTEM_PROMPT_JSON,
    FUNCTIONS_FOUND_USER_PROMPT,
    FnData,
)

variable_dict_from_llm_cpp = partial(
    VariableDict.dict_from_llm,
    VARIABLES_FOUND_SYSTEM_PROMPT_JSON,
    VARIABLES_FOUND_USER_PROMPT,
    VariableData,
)
