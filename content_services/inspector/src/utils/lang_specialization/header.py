from pathlib import Path
from typing import Self

from utils.codemap_ctags import extract_symbols_w_ctags
from utils.models import ChatOpenAI

from .ir_common import (
    ClassData,
    FnData,
    IrCollection,
    IrData,
    VariableData,
)
from .symbol_common import (
    ParserKind,
    RawSymbolCollection,
    RawSymbolData,
    ScopeRelation,
    SymbolKind,
    code_requires_multi_prompt,
    create_raw_symbol_via_ctags,
    default_ctags_analysis,
)

C_OR_CPP_HEADER_DATA_STRUCTURES = {"enum", "union", "struct", "class", "typedef"}
# TODO: Actually force `ctags` to return prototype kind information.
C_OR_CPP_HEADER_FUNCTIONS = {"function"}
C_OR_CPP_HEADER_MACROS = {"macro"}
C_OR_CPP_HEADER_VARIABLES = {"variable", "externvar"}


SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_C_OR_CPP_HEADER = """
You are an expert C and C++ programmer and a software engineering documentation expert. You write detailed documentation to explain code in C and C++ header files.

You are skilled at explaining technical details as well as recognize and articulate the key conceptual components and purpose of software.
"""

SOURCE_CODE_SMALL_SYSTEM_PROMPT_GENERAL_C_OR_CPP_HEADER = """
You are an expert C and C++ programmer and a software engineering documentation expert. You write detailed documentation to explain code in C and C++ header files.

You are skilled at explaining technical details as well as recognize and articulate the key conceptual components and purpose of software.

You specialize in effectively describing small and short source code files. Your goal is to be terse and clear, since the source code you are describing is small and simple.
"""

SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT = """
You will be given the source code contents of a header file. In 1 or 2 paragraphs, explain the purpose of the header file.

When writing your paragraphs, do not use speculative language.

When writing your paragraphs, consider questions like the following. You do not need to explicitly state these ideas, they are just given as examples of the kind of information to provide:

- Does the code provide narrow or broad functionality?
- What are the most important technical components?
- Is this code a collection of many different components? If so, what is the common theme or purpose?
- Does it define public APIs or external interfaces?
"""

SOURCE_CODE_SMALL_PURPOSE_USER_PROMPT = """
In a single paragraph of 3 to 5 sentences, explain the purpose of the header file code provided below.
"""

DATA_STRUCTURES_FOUND_SYSTEM_PROMPT_JSON = """
You are an expert systems programmer and a software engineering documentation expert. You write detailed documentation to explain C and C++ code, especially header files.

You focus on writing technical documentation for data structures such as structs, enums, and classes. You are skilled at explaining technical details as well as recognizing and articulating the key conceptual components and purpose of software.

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


FUNCTIONS_FOUND_SYSTEM_PROMPT_JSON = """
You are an expert systems programmer and a software engineering documentation expert. You write detailed documentation to explain C and C++ code, especially header files.

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


VARIABLES_FOUND_SYSTEM_PROMPT_JSON = """
You are an expert systems programmer and a software engineering documentation expert. You write detailed documentation to explain C and C++ code, especially header files.

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


# Symbol extraction classes
class HeaderDataStructureRawSymbolCollection(RawSymbolCollection):
    data: dict[str, RawSymbolData | list[RawSymbolData]]

    @classmethod
    def from_static_analysis(cls, code: str, root_rel_path: Path) -> Self:
        is_multi_prompt = code_requires_multi_prompt(code)

        symbols = extract_symbols_w_ctags(
            root_rel_path=root_rel_path, file_content=code
        )

        global_method_counts = {}
        class_raw_symbol_data = {}
        for s in symbols:
            if s["kind"] in C_OR_CPP_HEADER_FUNCTIONS and not s["name"].startswith(
                "__anon"
            ):
                global_method_counts[s["name"]] = (
                    global_method_counts.get(s["name"], 0) + 1
                )
            if s["kind"] in C_OR_CPP_HEADER_DATA_STRUCTURES and not s[
                "name"
            ].startswith("__anon"):
                use_padding = False
                if s["kind"] == "typedef":
                    use_padding = True
                class_raw_symbol_data[s["name"]] = create_raw_symbol_via_ctags(
                    ctags_symbol=s,
                    root_rel_path=root_rel_path,
                    code=code,
                    symbol_kind=SymbolKind.DATA_STRUCTURE,
                    scope_relation=None,
                    delimiter="::",
                    is_multi_prompt=is_multi_prompt,
                    use_padding=use_padding,
                )

        for s in symbols:
            if (
                (s.get("scope"))
                and not s["name"].startswith("__anon")
                and (s["kind"] in C_OR_CPP_HEADER_FUNCTIONS)
                and s["scopeKind"] in C_OR_CPP_HEADER_DATA_STRUCTURES
            ):
                if s["scope"].split("::")[-1] not in class_raw_symbol_data:
                    # Case where class is defined elsewhere (e.g. header), but methods for the class are defined in file
                    class_raw_symbol_data[s["scope"].split("::")[-1]] = RawSymbolData(
                        parser_kind=ParserKind.UCTAGS,
                        symbol_kind=SymbolKind.DATA_STRUCTURE,
                        name=s["scope"].split("::")[-1],
                        path=root_rel_path,
                        scope=None,
                        scope_relation=None,
                        children=[],
                        start_line=s["line"],
                        end_line=s["end"],
                        symbol_code=None,
                        file_code=None,
                        reference_code=None,
                        delimiter="::",
                    )

                is_overloaded = global_method_counts[s["name"]] > 1
                class_raw_symbol_data[s["scope"].split("::")[-1]].children.append(
                    create_raw_symbol_via_ctags(
                        ctags_symbol=s,
                        root_rel_path=root_rel_path,
                        code=code,
                        symbol_kind=SymbolKind.CALLABLE,
                        scope_relation=ScopeRelation.METHOD,
                        delimiter="::",
                        is_multi_prompt=is_multi_prompt,
                        is_overloaded=is_overloaded,
                    )
                )
            elif (
                (s.get("scope"))
                and not s["name"].startswith("__anon")
                and (s["kind"] in C_OR_CPP_HEADER_DATA_STRUCTURES)
                and (s["scopeKind"] in C_OR_CPP_HEADER_DATA_STRUCTURES)
            ):
                if s["scope"].split("::")[-1] in class_raw_symbol_data:
                    class_raw_symbol_data[s["scope"].split("::")[-1]].children.append(
                        create_raw_symbol_via_ctags(
                            ctags_symbol=s,
                            root_rel_path=root_rel_path,
                            code=code,
                            symbol_kind=SymbolKind.DATA_STRUCTURE,
                            scope_relation=ScopeRelation.NESTED_CLASS,
                            delimiter="::",
                            is_multi_prompt=is_multi_prompt,
                        )
                    )
        print(class_raw_symbol_data)
        output = (
            None if len(class_raw_symbol_data) == 0 else cls(data=class_raw_symbol_data)
        )
        return output

    @classmethod
    def from_llm(cls, code: str, root_rel_path: str) -> Self:
        raise NotImplementedError("Static analysis should be used for header functions")

    def to_dict(self) -> dict[str, RawSymbolData]:
        return self.data


class HeaderFnRawSymbolCollection(RawSymbolCollection):
    data: dict[str, RawSymbolData | list[RawSymbolData]]

    @classmethod
    def from_static_analysis(cls, code: str, root_rel_path: Path) -> Self:
        is_multi_prompt = code_requires_multi_prompt(code)

        symbols = extract_symbols_w_ctags(
            root_rel_path=root_rel_path, file_content=code
        )

        all_fn_names = [
            s["name"]
            for s in symbols
            if s["kind"] in C_OR_CPP_HEADER_FUNCTIONS
            and not s["name"].startswith("__anon")
        ]

        fn_raw_symbol_data = {}
        for s in symbols:
            if s["kind"] in C_OR_CPP_HEADER_FUNCTIONS and not s["name"].startswith(
                "__anon"
            ):
                contained_in_class = False
                if (s.get("scope")) and (
                    s.get("scopeKind") in C_OR_CPP_HEADER_DATA_STRUCTURES
                ):
                    contained_in_class = True

                fn_name = (
                    s["name"]
                    if s.get("scopeKind") not in C_OR_CPP_HEADER_DATA_STRUCTURES
                    else s["scope"].split("::")[-1] + "::" + s["name"]
                )
                s["name"] = fn_name
                if not contained_in_class and all_fn_names.count(s["name"]) == 1:
                    if fn_name not in fn_raw_symbol_data:
                        fn_raw_symbol_data[fn_name] = []
                    fn_raw_symbol_data[fn_name].append(
                        create_raw_symbol_via_ctags(
                            ctags_symbol=s,
                            root_rel_path=root_rel_path,
                            code=code,
                            symbol_kind=SymbolKind.CALLABLE,
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
                        create_raw_symbol_via_ctags(
                            ctags_symbol=s,
                            root_rel_path=root_rel_path,
                            code=code,
                            symbol_kind=SymbolKind.CALLABLE,
                            scope_relation=None,
                            delimiter="::",
                            is_multi_prompt=is_multi_prompt,
                            is_overloaded=True,
                        )
                    )
        output = None if len(fn_raw_symbol_data) == 0 else cls(data=fn_raw_symbol_data)
        return output

    @classmethod
    def from_llm(cls, code: str, root_rel_path: str) -> Self:
        raise NotImplementedError("Static analysis should be used for header functions")

    def to_dict(self) -> dict[str, RawSymbolData]:
        return self.data


class HeaderVariableRawSymbolCollection(RawSymbolCollection):
    data: dict[str, RawSymbolData | list[RawSymbolData]]

    @classmethod
    def from_static_analysis(cls, code: str, root_rel_path: Path) -> Self | None:
        return default_ctags_analysis(
            collection_cls=cls,
            code=code,
            root_rel_path=root_rel_path,
            symbol_kind=SymbolKind.VARIABLE,
            ctags_kinds=C_OR_CPP_HEADER_VARIABLES,
            delimiter="::",
            add_symbol_padding=True,
        )

    @classmethod
    def from_llm(cls, code: str, root_rel_path: str) -> Self:
        raise NotImplementedError("Static analysis should be used for header variables")

    def to_dict(self) -> dict[str, RawSymbolData]:
        return self.data


class HeaderDataStructureData(ClassData):
    @classmethod
    def system_prompt(cls) -> str:
        return DATA_STRUCTURES_FOUND_SYSTEM_PROMPT_JSON

    @classmethod
    def user_prompt(cls, symbol: RawSymbolData) -> str:
        user_prompt = f"{DATA_STRUCTURES_FOUND_USER_PROMPT}{symbol.name}\n\nCode containing Data Structure:\n\n{symbol.symbol_code}"
        if symbol.file_code:
            user_prompt += f"\n\nFull File Code:\n\n{symbol.file_code}"
        return user_prompt

    @classmethod
    def child_to_ir(cls, symbol: RawSymbolData) -> type[IrData] | None:
        mapping = {
            SymbolKind.CALLABLE: HeaderFnData,
            SymbolKind.DATA_STRUCTURE: None,  # for child classes and structs we just list them
        }
        return mapping.get(symbol.symbol_kind)

    @classmethod
    def child_to_field_name(cls, child: RawSymbolData) -> str:
        mapping = {
            SymbolKind.CALLABLE: "Methods",
            SymbolKind.DATA_STRUCTURE: "Nested Classes",
        }
        return mapping.get(child.symbol_kind)


class HeaderDataStructureCollection(IrCollection):
    data: dict[str, HeaderDataStructureData | list[HeaderDataStructureData]]

    @classmethod
    def from_llm(cls, llm: ChatOpenAI, symbols_list: RawSymbolCollection) -> Self:
        return cls.from_llm_with_ir_data(HeaderDataStructureData, llm, symbols_list)


class HeaderFnData(FnData):
    @classmethod
    def system_prompt(cls) -> str:
        return FUNCTIONS_FOUND_SYSTEM_PROMPT_JSON

    @classmethod
    def user_prompt(cls, symbol: RawSymbolData) -> str:
        user_prompt = f"{FUNCTIONS_FOUND_USER_PROMPT}{symbol.name}\n\nFunction Code:\n\n{symbol.symbol_code}"
        if symbol.file_code:
            user_prompt += f"\n\nFull File Code:\n\n{symbol.file_code}"
        return user_prompt

    @classmethod
    def child_to_ir(cls, symbol: RawSymbolData) -> type[IrData] | None:
        raise NotImplementedError("Functions should not have children")

    @classmethod
    def child_to_field_name(cls, child: RawSymbolData) -> str:
        raise NotImplementedError("Functions should not have children")


class HeaderFnCollection(IrCollection):
    data: dict[str, HeaderFnData | list[HeaderFnData]]

    @classmethod
    def from_llm(cls, llm: ChatOpenAI, symbols_list: RawSymbolCollection) -> Self:
        return cls.from_llm_with_ir_data(HeaderFnData, llm, symbols_list)


class HeaderVariableData(VariableData):
    @classmethod
    def system_prompt(cls) -> str:
        return VARIABLES_FOUND_SYSTEM_PROMPT_JSON

    @classmethod
    def user_prompt(cls, symbol: RawSymbolData) -> str:
        user_prompt = f"{VARIABLES_FOUND_USER_PROMPT}{symbol.name}\n\nVariable Code:\n\n{symbol.symbol_code}"
        if symbol.file_code:
            user_prompt += f"\n\nFull File Code:\n\n{symbol.file_code}"
        return user_prompt

    @classmethod
    def child_to_ir(cls, symbol: RawSymbolData) -> type[IrData] | None:
        raise NotImplementedError("Variables should not have children")

    @classmethod
    def child_to_field_name(cls, child: RawSymbolData) -> str:
        raise NotImplementedError("Variables should not have children")


class HeaderVariableCollection(IrCollection):
    data: dict[str, HeaderVariableData | list[HeaderVariableData]]

    @classmethod
    def from_llm(cls, llm: ChatOpenAI, symbols_list: RawSymbolCollection) -> Self:
        return cls.from_llm_with_ir_data(HeaderVariableData, llm, symbols_list)
