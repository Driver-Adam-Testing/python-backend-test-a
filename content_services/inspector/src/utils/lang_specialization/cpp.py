from pathlib import Path
from typing import Self

from pydantic import PrivateAttr
from utils.models import ChatOpenAI
from utils.treesitter_drivers.c_cpp_driver import CppCDriverTree

from ..symbol_table.utils import get_fully_qualified_name
from .ir_common import (
    FieldNameWithBackTickContent,
    FieldNameWithRawContent,
    FnData,
    IrCollection,
    IrData,
    ListedBacktickNameRawContentNoNone,
    VariableData,
)
from .symbol_common import (
    ParserKind,
    RawSymbolCollection,
    RawSymbolData,
    ReifiedSymbol,
    ScopeRelation,
    SymbolKind,
    code_requires_multi_prompt,
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
}
IMPORTANT: Members should ONLY include attributes, fields, or properties of the data structure. Do not include methods, class functions, or any function declarations in the members list of the data structure.

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


# Ir Data Classes
class CppVariableData(VariableData):
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


class CppVariableCollection(IrCollection):
    data: dict[str, CppVariableData | list[CppVariableData]]

    @classmethod
    def from_llm(cls, llm: ChatOpenAI, symbols_list: RawSymbolCollection) -> Self:
        return cls.from_llm_with_ir_data(CppVariableData, llm, symbols_list)


class CppFnData(FnData):
    @classmethod
    def system_prompt(cls) -> str:
        return FUNCTIONS_FOUND_SYSTEM_PROMPT_JSON

    @classmethod
    def user_prompt(cls, symbol: RawSymbolData) -> str:
        user_prompt = f"{FUNCTIONS_FOUND_USER_PROMPT}{symbol.name}\n\nFunction Code:\n\n{symbol.symbol_code}"
        if (
            symbol.reified_symbol is not None
            and symbol.reified_symbol.parent is not None
            and symbol.reified_symbol.parent.raw.symbol_code is not None
        ):
            user_prompt += f"\n\nParent data structure code:\n\n{symbol.reified_symbol.parent.raw.symbol_code}"
        if symbol.file_code:
            user_prompt += f"\n\nFull File Code:\n\n{symbol.file_code}"
        return user_prompt

    @classmethod
    def child_to_ir(cls, symbol: RawSymbolData) -> type[IrData] | None:
        raise NotImplementedError("Functions should not have children")

    @classmethod
    def child_to_field_name(cls, child: RawSymbolData) -> str:
        raise NotImplementedError("Functions should not have children")


class CppFnCollection(IrCollection):
    data: dict[str, CppFnData | list[CppFnData]]

    @classmethod
    def from_llm(cls, llm: ChatOpenAI, symbols_list: RawSymbolCollection) -> Self:
        return cls.from_llm_with_ir_data(CppFnData, llm, symbols_list)


class CppDataStructureData(IrData):
    type: FieldNameWithBackTickContent
    members: ListedBacktickNameRawContentNoNone
    description: FieldNameWithRawContent
    _supported_child_ordering: list[str] = PrivateAttr(
        default=[ScopeRelation.METHOD, ScopeRelation.NESTED_CLASS]
    )

    @classmethod
    def default_instance(cls, reified_symbol: ReifiedSymbol | None = None) -> Self:
        if reified_symbol is not None:
            name_part = get_fully_qualified_name(reified_symbol.raw)
            kind_part = reified_symbol.raw.symbol_kind.name.lower()
            path_part = reified_symbol.raw.file_path
            link = f"[See definition]({path_part}#{kind_part}:{name_part})"
            return cls(
                description=FieldNameWithRawContent(content=link),
                type=FieldNameWithBackTickContent(content=""),
                members=ListedBacktickNameRawContentNoNone(content=[]),
            )
        return cls(
            description=FieldNameWithRawContent(content=""),
            type=FieldNameWithBackTickContent(content=""),
            members=ListedBacktickNameRawContentNoNone(content=[]),
        )

    @classmethod
    def system_prompt(cls) -> str:
        return DATA_STRUCTURES_FOUND_SYSTEM_PROMPT_JSON

    @classmethod
    def user_prompt(cls, symbol: RawSymbolData) -> str:
        user_prompt = f"{DATA_STRUCTURES_FOUND_USER_PROMPT}{symbol.name}\n\nCode containing Data Structure:\n\n{symbol.symbol_code}"
        if len(symbol.reified_symbol.children) > 0:
            user_prompt += (
                "\n\nCode of data structure functions defined outside the file:"
            )
            for child in symbol.reified_symbol.children:
                if child.raw.file_path != symbol.reified_symbol.raw.file_path:
                    user_prompt += f"\n\n{child.raw.symbol_code}"
        if symbol.file_code:
            user_prompt += f"\n\nFull File Code:\n\n{symbol.file_code}"
        return user_prompt

    @classmethod
    def child_to_ir(cls, symbol: RawSymbolData) -> type[IrData] | None:
        mapping = {
            SymbolKind.CALLABLE: CppFnData,
            SymbolKind.DATA_STRUCTURE: None,  # for child classes and structs we just list them
        }
        return mapping.get(symbol.symbol_kind)

    @classmethod
    def child_to_field_name(cls, child: RawSymbolData) -> str:
        mapping = {
            SymbolKind.CALLABLE: ScopeRelation.METHOD,
            SymbolKind.DATA_STRUCTURE: ScopeRelation.NESTED_CLASS,
        }
        return mapping.get(child.symbol_kind)


class CppDataStructureCollection(IrCollection):
    data: dict[str, CppDataStructureData | list[CppDataStructureData]]

    @classmethod
    def from_llm(cls, llm: ChatOpenAI, symbols_list: RawSymbolCollection) -> Self:
        return cls.from_llm_with_ir_data(CppDataStructureData, llm, symbols_list)


# Symbol Extraction Classes
class CppDataStructureRawSymbolCollection(RawSymbolCollection):
    data: dict[str, RawSymbolData]

    @classmethod
    def from_static_analysis(
        cls, code: str, root_rel_path: Path, reified_symbols: list[ReifiedSymbol]
    ) -> Self | None:
        # driver_tree = CppCDriverTree.from_code(code, root_rel_path)
        ds_symbols = [
            sym
            for sym in reified_symbols
            if sym.raw.symbol_kind == SymbolKind.DATA_STRUCTURE and sym.is_definition
        ]
        data_structure_raw_symbol_data = {}
        is_large_file = code_requires_multi_prompt(code)

        for ds_symbol in ds_symbols:
            if ds_symbol.raw.name is not None:
                raw_symbol_data = RawSymbolData.from_tree_sitter_raw_symbol(
                    ts_symbol=ds_symbol.raw,
                    path=root_rel_path,
                    scope=None,
                    scope_relation=None,
                    children=[],
                    reference_code=None,
                    delimiter="::",
                    is_large_file=is_large_file,
                    is_overloaded=False,
                    use_padding=False,
                    code=code,
                    reified_symbol=ds_symbol,
                )
                for child in ds_symbol.children:
                    if (
                        child.raw.symbol_kind == SymbolKind.CALLABLE
                        and child.raw.file_path
                        == ds_symbol.raw.file_path  # NOTE: This means that only children in the same file will be documented in the scope of the class
                    ):
                        raw_symbol_data.children.append(
                            RawSymbolData.from_tree_sitter_raw_symbol(
                                ts_symbol=child.raw,
                                path=root_rel_path,
                                scope=ds_symbol.raw.name,
                                scope_relation=ScopeRelation.METHOD,
                                children=[],
                                reference_code=None,
                                delimiter="::",
                                is_large_file=is_large_file,
                                is_overloaded=False,
                                use_padding=False,
                                code=code,
                                reified_symbol=child,
                            )
                        )
                data_structure_raw_symbol_data[ds_symbol.raw.name] = raw_symbol_data
        callable_symbols_with_parent = [
            sym
            for sym in reified_symbols
            if sym.raw.symbol_kind == SymbolKind.CALLABLE and sym.parent is not None
        ]
        for callable_symbol in callable_symbols_with_parent:
            if callable_symbol.parent.raw.symbol_kind == SymbolKind.DATA_STRUCTURE:
                parent_name = callable_symbol.parent.raw.name
                if parent_name not in data_structure_raw_symbol_data:
                    data_structure_raw_symbol_data[parent_name] = RawSymbolData(
                        parser_kind=ParserKind.TREE_SITTER,
                        symbol_kind=SymbolKind.DATA_STRUCTURE,
                        name=parent_name,
                        path=root_rel_path,
                        scope=None,
                        scope_relation=None,
                        children=[],
                        start_line=0,
                        end_line=0,
                        symbol_code=None,
                        file_code=None,
                        reference_code=None,
                        delimiter="::",
                        reified_symbol=callable_symbol.parent,
                    )
                if (
                    callable_symbol.raw.name is not None
                    and callable_symbol.raw.name
                    not in [
                        child.name
                        for child in data_structure_raw_symbol_data[
                            parent_name
                        ].children
                    ]
                ):
                    data_structure_raw_symbol_data[parent_name].children.append(
                        RawSymbolData.from_tree_sitter_raw_symbol(
                            ts_symbol=callable_symbol.raw,
                            path=root_rel_path,
                            scope=parent_name,
                            scope_relation=ScopeRelation.METHOD,
                            children=[],
                            reference_code=None,
                            delimiter="::",
                            is_large_file=is_large_file,
                            is_overloaded=False,
                            use_padding=False,
                            code=code,
                            reified_symbol=callable_symbol,
                        )
                    )
        output = (
            None
            if len(data_structure_raw_symbol_data) == 0
            else cls(data=data_structure_raw_symbol_data)
        )
        return output

    @classmethod
    def from_llm(cls, code: str, root_rel_path: str) -> Self:
        raise NotImplementedError(
            "Static analysis should be used for C data structures"
        )

    def to_dict(self) -> dict[str, RawSymbolData]:
        return self.data


class CppFreeFnRawSymbolCollection(RawSymbolCollection):
    data: dict[str, RawSymbolData]

    @classmethod
    def from_static_analysis(
        cls, code: str, root_rel_path: Path, reified_symbols: list[ReifiedSymbol] | None
    ) -> Self | None:
        func_symbols = [
            sym for sym in reified_symbols if sym.raw.symbol_kind == SymbolKind.CALLABLE
        ]

        function_raw_symbol_data = {}
        is_large_file = code_requires_multi_prompt(code)

        for reified_sym in func_symbols:
            symbol_parent_kind = (
                reified_sym.parent.raw.symbol_kind if reified_sym.parent else None
            )
            ts_symbol = reified_sym.raw
            if (
                ts_symbol.name is not None
                and symbol_parent_kind != SymbolKind.DATA_STRUCTURE
            ):
                raw_symbol_data = RawSymbolData.from_tree_sitter_raw_symbol(
                    ts_symbol=ts_symbol,
                    path=root_rel_path,
                    scope=None,
                    scope_relation=None,
                    children=[],
                    reference_code=None,
                    delimiter=None,
                    is_large_file=is_large_file,
                    is_overloaded=False,
                    use_padding=False,
                    code=code,
                    reified_symbol=reified_sym,  # TODO hack!
                )
                function_raw_symbol_data[ts_symbol.name] = raw_symbol_data

        output = (
            None
            if len(function_raw_symbol_data) == 0
            else cls(data=function_raw_symbol_data)
        )
        return output

    @classmethod
    def from_llm(cls, code: str, root_rel_path: str) -> Self:
        raise NotImplementedError("Static analysis should be used for C functions")

    def to_dict(self) -> dict[str, RawSymbolData]:
        return self.data


class CppVariableRawSymbolCollection(RawSymbolCollection):
    data: dict[str, RawSymbolData]

    @classmethod
    def from_static_analysis(cls, code: str, root_rel_path: Path) -> Self | None:
        driver_tree = CppCDriverTree.from_code(code, root_rel_path)
        variable_raw_symbol_data = {}
        is_large_file = code_requires_multi_prompt(code)

        for ts_symbol in driver_tree.extract_variables():
            if ts_symbol.name is not None:
                raw_symbol_data = RawSymbolData.from_tree_sitter_raw_symbol(
                    ts_symbol=ts_symbol,
                    path=root_rel_path,
                    scope=None,
                    scope_relation=None,
                    children=[],
                    reference_code=None,
                    delimiter=None,
                    is_large_file=is_large_file,
                    is_overloaded=False,
                    use_padding=False,
                    code=code,
                )
                variable_raw_symbol_data[ts_symbol.name] = raw_symbol_data

        output = (
            None
            if len(variable_raw_symbol_data) == 0
            else cls(data=variable_raw_symbol_data)
        )
        return output

    @classmethod
    def from_llm(cls, code: str, root_rel_path: str) -> Self:
        raise NotImplementedError("Static analysis should be used for C variables")

    def to_dict(self) -> dict[str, RawSymbolData]:
        return self.data


# TODO: Make a base class in `ir_common.py` that just takes in a tree.
class CppIncludeRawSymbolCollection(RawSymbolCollection):
    data: dict[str, RawSymbolData]

    @classmethod
    def from_static_analysis(cls, code: str, root_rel_path: Path) -> Self | None:
        driver_tree = CppCDriverTree.from_code(code, root_rel_path)
        is_large_file = code_requires_multi_prompt(code)

        import_dict = {}
        for ts_symbol in driver_tree.extract_imports():
            raw_symbol_data = RawSymbolData.from_tree_sitter_raw_symbol(
                ts_symbol=ts_symbol,
                path=root_rel_path,
                scope=None,
                scope_relation=None,
                children=[],
                reference_code=None,
                delimiter=None,
                is_large_file=is_large_file,
                is_overloaded=False,
                use_padding=False,
                code=code,
            )
            import_dict[ts_symbol.name] = raw_symbol_data
        output = None if len(import_dict) == 0 else cls(data=import_dict)
        return output

    @classmethod
    def from_llm(cls, code: str, root_rel_path: str) -> Self:
        raise NotImplementedError("Static analysis should be used for c++ imports")

    def to_dict(self) -> dict[str, RawSymbolData]:
        return self.data
