from functools import partial
from pathlib import Path
from typing import Self

from pydantic import PrivateAttr
from utils.codemap_ctags import extract_symbols_w_ctags

from .ir_common import (
    FieldNameWithRawContent,
    FnData,
    IrCollection,
    IrData,
)
from .symbol_common import (
    RawSymbolCollection,
    RawSymbolData,
    ScopeRelation,
    SymbolKind,
    code_requires_multi_prompt,
    create_raw_symbol_via_ctags,
)

C_SHARP_CLASSES = {"class"}
C_SHARP_DATA_STRUCTURES = {"struct"}
C_SHARP_FUNCTIONS = {"method"}
C_SHARP_INTERFACES = {"interface"}
C_SHARP_VARIABLES = {"field", "property"}
C_SHARP_ENUMS = {"enum"}
C_SHARP_ENUM_VALS = {"enumerator"}


SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_CS = """
You are an expert C# programmer and a software engineering documentation expert. You write detailed documentation to explain code written in C#.

You are skilled at explaining technical details as well as recognize and articulate the key conceptual components and purpose of software.
"""

SOURCE_CODE_SMALL_SYSTEM_PROMPT_GENERAL_CS = """
You are an expert C# programmer and a software engineering documentation expert. You write detailed documentation to explain code written in C#.

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
- What kind of code is this? For example, is this code clearly an executable (e.g., main.cs), a C# file or library intended to be imported elsewhere?
- Does it define public APIs or external interfaces?
"""

SOURCE_CODE_SMALL_PURPOSE_USER_PROMPT = """
In a single paragraph of 3 to 5 sentences, explain the purpose of the code provided below. Consider questions such as the following when providing your output:

- Does this code provide narrow or broad functionality?
- What kind of code is this? For example, is this code clearly an executable (e.g., main.cs), a C# file or library intended to be imported elsewhere?
"""

CLASSES_FOUND_SYSTEM_PROMPT_JSON = """
You are an expert C# programmer and a software engineering documentation expert. You write detailed documentation to explain code written in C#.

You focus on writing technical documentation for classes in C#. You are skilled at explaining technical details as well as recognizing and articulating the key conceptual components and purpose of software.

You will be given the name of a class to document and the source code where the class is defined.

Your job is to describe the class. **Always respond using exactly the following JSON schema**:
{
    "description": <one paragraph description of the data structure>,
    "inherits_from": [<list of parent classes or structs>],
    "implements": [<list of interfaces implemented>],
    "modifiers": [<list of modifiers of the class, e.g. new, public, private, protected, internal, abstract, sealed, or static. Can be an empty list.>],
}

Return JSON according to the schema above. Do not use the format ```json ... ```, just return the JSON data.
"""

CLASSES_FOUND_USER_PROMPT = """
Summarize the class in the code provided below.

- When describing an important class, provide detail that matches the complexity of the class. Large and complex class should get longer explanations, while small ones a single sentence.

Class to document:
"""

INTERFACES_FOUND_SYSTEM_PROMPT_JSON = """
You are an expert C# programmer and a software engineering documentation expert. You write detailed documentation to explain code written in C#.

You focus on writing technical documentation for interfaces in C#. You are skilled at explaining technical details as well as recognizing and articulating the key conceptual components and purpose of software.

You will be given the name of a interface to document and the source code where the interface is defined.

Your job is to describe the interface. **Always respond using exactly the following JSON schema**:
{
    "interfaces_inherited": [<list of interfaces inherited from>]
    "description": <one paragraph description of the interface>,
}

Return JSON according to the schema above. Do not use the format ```json ... ```, just return the JSON data.
"""

INTERFACES_FOUND_USER_PROMPT = """
Summarize the interface in the code provided below.

Interface to document:
"""

STRUCTS_FOUND_SYSTEM_PROMPT_JSON = """
You are an expert C# programmer and a software engineering documentation expert. You write detailed documentation to explain code written in C#.

You focus on writing technical documentation for structs in C#. You are skilled at explaining technical details as well as recognizing and articulating the key conceptual components and purpose of software.

You will be given the name of a struct to document and the source code where the struct is defined.

Your job is to describe the struct. **Always respond using exactly the following JSON schema**:
{
    "description": <one paragraph description of the data structure>,
    "implements": [<list of interfaces implemented>],
    "modifiers": [<list of modifiers of the class, e.g. new, public, private, protected, internal, abstract, sealed, or static. Can be an empty list.>],
}

Return JSON according to the schema above. Do not use the format ```json ... ```, just return the JSON data.
"""

STRUCTS_FOUND_USER_PROMPT = """
Summarize the struct in the code provided below.

- When describing an important struct, provide detail that matches the complexity of the class. Large and complex class should get longer explanations, while small ones a single sentence.

Struct to document:
"""

METHODS_FOUND_SYSTEM_PROMPT_JSON = """
You are an expert C# programmer and a software engineering documentation expert. You write detailed documentation to explain code written in C#.

You focus on writing technical documentation for methods. You are skilled at explaining technical details as well as recognizing and articulating the key conceptual components and purpose of software.

You will be given the name of a method to document and the source code where the method is defined.

Your job is to describe the method. **Always respond using exactly the following JSON schema**:
{
    "single_sentence": <terse single sentence description of the method>,
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
    "output": <description of output>,
}

Return JSON according to the schema above. Do not use the format ```json ... ```, just return the JSON data.
"""

METHODS_FOUND_USER_PROMPT = """
Summarize the method in the code provided below. Describe the inputs, control flow and logic, and output.

- When describing a method, provide detail that matches the complexity of the method body. Large and complex methods should get longer explanations, while small ones much less.

Method to document:
"""

VARIABLES_FOUND_SYSTEM_PROMPT_JSON = """
You are an expert C# programmer and a software engineering documentation expert. You write detailed documentation to explain code written in C#.

You focus on writing technical documentation for variables. You are skilled at explaining technical details as well as recognizing and articulating the key conceptual components and purpose of software.

You will be given the name of a variable to document and the source code where the data structure is defined.

Your job is to describe the data structure. **Always respond using exactly the following JSON schema**:
{
    "description": <1 sentence description of the variable>,
}

Return JSON according to the schema above. Do not use the format ```json ... ```, just return the JSON data.
"""

VARIABLES_FOUND_USER_PROMPT = """
Summarize the variable in the code provided below.

Variable to document:
"""

ENUMS_FOUND_SYSTEM_PROMPT_JSON = """
You are an expert C# programmer and a software engineering documentation expert. You write detailed documentation to explain code written in C#.

You focus on writing technical documentation for enums. You are skilled at explaining technical details as well as recognizing and articulating the key conceptual components and purpose of software.

You will be given the name of a enum to document and the source code where the enum is defined.

Your job is to describe the enum. **Always respond using exactly the following JSON schema**:
{
    "description": <2 sentence description of the enum.>,
}

Return JSON according to the schema above. Do not use the format ```json ... ```, just return the JSON data.
"""

ENUMS_FOUND_USER_PROMPT = """
Summarize the enum in the code provided below.

Enum to document:
"""


# Ir Data Classes
class CsEnumData(IrData):
    description: FieldNameWithRawContent
    _supported_child_ordering: list[str] = PrivateAttr(
        default=[
            ScopeRelation.ENUMERATOR,
        ]
    )

    @classmethod
    def system_prompt(cls) -> str:
        return ENUMS_FOUND_SYSTEM_PROMPT_JSON

    @classmethod
    def user_prompt(cls, symbol: RawSymbolData) -> str:
        user_prompt = f"{ENUMS_FOUND_USER_PROMPT}{symbol.name}\n\nEnum Code:\n\n{symbol.symbol_code}"
        if symbol.file_code:
            user_prompt += f"\n\nFull File Code:\n\n{symbol.file_code}"
        return user_prompt

    @classmethod
    def child_to_ir(cls, symbol: RawSymbolData) -> type[IrData] | None:
        mapping = {
            SymbolKind.VARIABLE: None,
        }
        return mapping.get(symbol.symbol_kind)

    @classmethod
    def child_to_field_name(cls, child: RawSymbolData) -> str:
        mapping = {
            SymbolKind.VARIABLE: ScopeRelation.ENUMERATOR,
        }
        return mapping.get(child.symbol_kind)

    @classmethod
    def default_instance(cls) -> Self:
        return cls(description="")


class CsEnumCollection(IrCollection):
    data: dict[str, CsEnumData | list[CsEnumData]]


class CsVariableData(IrData):
    description: FieldNameWithRawContent

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

    @classmethod
    def default_instance(cls) -> Self:
        return cls(description="")


class CsMethodData(FnData):
    @classmethod
    def system_prompt(cls) -> str:
        return METHODS_FOUND_SYSTEM_PROMPT_JSON

    @classmethod
    def user_prompt(cls, symbol: RawSymbolData) -> str:
        user_prompt = f"{METHODS_FOUND_USER_PROMPT}{symbol.name}\n\nMethod Code:\n\n{symbol.symbol_code}"
        if symbol.file_code:
            user_prompt += f"\n\nFull File Code:\n\n{symbol.file_code}"
        return user_prompt

    @classmethod
    def child_to_ir(cls, symbol: RawSymbolData) -> type[IrData] | None:
        raise NotImplementedError("Methods should not have children")

    @classmethod
    def child_to_field_name(cls, child: RawSymbolData) -> str:
        raise NotImplementedError("Methods should not have children")


class CsStructData(IrData):
    description: FieldNameWithRawContent
    implements: list[str]
    modifiers: list[str]
    # TODO: support for Fields/internal variables instead of the members field
    _supported_child_ordering: list[str] = PrivateAttr(
        default=[
            ScopeRelation.FIELD,
            ScopeRelation.METHOD,
            ScopeRelation.NESTED_CLASS,
        ]
    )

    @classmethod
    def system_prompt(cls) -> str:
        return STRUCTS_FOUND_SYSTEM_PROMPT_JSON

    @classmethod
    def user_prompt(cls, symbol: RawSymbolData) -> str:
        user_prompt = f"{STRUCTS_FOUND_USER_PROMPT}{symbol.name}\n\nStruct Code:\n\n{symbol.symbol_code}"
        if symbol.file_code:
            user_prompt += f"\n\nFull File Code:\n\n{symbol.file_code}"
        return user_prompt

    @classmethod
    def child_to_ir(cls, symbol: RawSymbolData) -> type[IrData] | None:
        mapping = {
            SymbolKind.CALLABLE: CsMethodData,
            SymbolKind.DATA_STRUCTURE: None,  # for child classes and structs we just list them
            SymbolKind.CLASS: None,
            SymbolKind.VARIABLE: CsVariableData,
        }
        return mapping.get(symbol.symbol_kind)

    @classmethod
    def child_to_field_name(cls, child: RawSymbolData) -> str:
        mapping = {
            SymbolKind.CALLABLE: ScopeRelation.METHOD,
            SymbolKind.DATA_STRUCTURE: ScopeRelation.NESTED_CLASS,
            SymbolKind.CLASS: ScopeRelation.NESTED_CLASS,
            SymbolKind.VARIABLE: ScopeRelation.FIELD,
        }
        return mapping.get(child.symbol_kind)

    @classmethod
    def default_instance(cls) -> Self:
        return cls(
            description="",
            implements=[],
            modifiers=[],
        )


class CsStructCollection(IrCollection):
    data: dict[str, CsStructData | list[CsStructData]]


class CsClassData(IrData):
    description: FieldNameWithRawContent
    inherits_from: list[str]
    implements: list[str]
    modifiers: list[str]
    # TODO: support for Fields/internal variables instead of the members field
    _supported_child_ordering: list[str] = PrivateAttr(
        default=[
            ScopeRelation.FIELD,
            ScopeRelation.METHOD,
            ScopeRelation.NESTED_CLASS,
        ]
    )

    @classmethod
    def system_prompt(cls) -> str:
        return CLASSES_FOUND_SYSTEM_PROMPT_JSON

    @classmethod
    def user_prompt(cls, symbol: RawSymbolData) -> str:
        user_prompt = f"{CLASSES_FOUND_USER_PROMPT}{symbol.name}\n\nClass Code:\n\n{symbol.symbol_code}"
        if symbol.file_code:
            user_prompt += f"\n\nFull File Code:\n\n{symbol.file_code}"
        return user_prompt

    @classmethod
    def child_to_ir(cls, symbol: RawSymbolData) -> type[IrData] | None:
        mapping = {
            SymbolKind.CALLABLE: CsMethodData,
            SymbolKind.DATA_STRUCTURE: None,  # for child classes and structs we just list them
            SymbolKind.CLASS: None,
            SymbolKind.VARIABLE: CsVariableData,
        }
        return mapping.get(symbol.symbol_kind)

    @classmethod
    def child_to_field_name(cls, child: RawSymbolData) -> str:
        mapping = {
            SymbolKind.CALLABLE: ScopeRelation.METHOD,
            SymbolKind.DATA_STRUCTURE: ScopeRelation.NESTED_CLASS,
            SymbolKind.CLASS: ScopeRelation.NESTED_CLASS,
            SymbolKind.VARIABLE: ScopeRelation.FIELD,
        }
        return mapping.get(child.symbol_kind)

    @classmethod
    def default_instance(cls) -> Self:
        return cls(
            description="",
            inherits_from=[],
            implements=[],
            modifiers=[],
        )


class CsClassCollection(IrCollection):
    data: dict[str, CsClassData | list[CsClassData]]


class CsInterfaceData(IrData):
    interfaces_inherited: list[str]
    description: FieldNameWithRawContent
    _supported_child_ordering: list[str] = PrivateAttr(
        default=[
            ScopeRelation.FIELD,
            ScopeRelation.METHOD,
        ]
    )

    @classmethod
    def system_prompt(cls) -> str:
        return INTERFACES_FOUND_SYSTEM_PROMPT_JSON

    @classmethod
    def user_prompt(cls, symbol: RawSymbolData) -> str:
        user_prompt = f"{INTERFACES_FOUND_USER_PROMPT}{symbol.name}\n\nInterface Code:\n\n{symbol.symbol_code}"
        if symbol.file_code:
            user_prompt += f"\n\nFull File Code:\n\n{symbol.file_code}"
        return user_prompt

    @classmethod
    def child_to_ir(cls, symbol: RawSymbolData) -> type[IrData] | None:
        mapping = {
            SymbolKind.VARIABLE: CsVariableData,
            SymbolKind.CALLABLE: None,  # we don't document the functions, since they're just an interface
        }
        return mapping.get(symbol.symbol_kind)

    @classmethod
    def child_to_field_name(cls, child: RawSymbolData) -> str:
        mapping = {
            SymbolKind.CALLABLE: ScopeRelation.METHOD,
            SymbolKind.VARIABLE: ScopeRelation.FIELD,
        }
        return mapping.get(child.symbol_kind)

    @classmethod
    def default_instance(cls) -> Self:
        return cls(
            interfaces_inherited=[],
            description="",
        )


class CsInterfaceCollection(IrCollection):
    data: dict[str, CsInterfaceData | list[CsInterfaceData]]


# Symbol Extraction Classes
class CsClassRawSymbolCollection(RawSymbolCollection):
    data: dict[str, RawSymbolData]

    @classmethod
    def from_static_analysis(cls, code: str, root_rel_path: Path) -> Self | None:
        is_multi_prompt = code_requires_multi_prompt(code)

        symbols = extract_symbols_w_ctags(
            root_rel_path=root_rel_path, file_content=code
        )

        global_method_counts = {}
        class_raw_symbol_data = {}
        for s in symbols:
            if s["kind"] in C_SHARP_FUNCTIONS and not s["name"].startswith("__anon"):
                global_method_counts[s["name"]] = (
                    global_method_counts.get(s["name"], 0) + 1
                )
            if s["kind"] in C_SHARP_CLASSES and not s["name"].startswith("__anon"):
                class_raw_symbol_data[s["name"]] = create_raw_symbol_via_ctags(
                    ctags_symbol=s,
                    root_rel_path=root_rel_path,
                    code=code,
                    symbol_kind=SymbolKind.CLASS,
                    scope_relation=None,
                    delimiter=".",
                    is_multi_prompt=is_multi_prompt,
                )

        for s in symbols:
            if (
                (s.get("scope"))
                and not s["name"].startswith("__anon")
                and (s["kind"] in C_SHARP_FUNCTIONS)
                and s["scopeKind"] in C_SHARP_CLASSES
            ):
                # TODO: is this needed for partial case?
                # if s["scope"].split("::")[-1] not in class_raw_symbol_data:
                #     # Case where class is defined elsewhere (e.g. header), but methods for the class are defined in file
                #     class_raw_symbol_data[s["scope"].split("::")[-1]] = RawSymbolData(
                #         parser_kind=ParserKind.UCTAGS,
                #         symbol_kind=SymbolKind.DATA_STRUCTURE,
                #         name=s["scope"].split("::")[-1],
                #         path=root_rel_path,
                #         scope=None,
                #         scope_relation=None,
                #         children=[],
                #         start_line=s["line"],
                #         end_line=s["end"],
                #         symbol_code=None,
                #         file_code=None,
                #         reference_code=None,
                #         delimiter=".",
                #     )

                is_overloaded = global_method_counts[s["name"]] > 1
                class_raw_symbol_data[s["scope"].split(".")[-1]].children.append(
                    create_raw_symbol_via_ctags(
                        ctags_symbol=s,
                        root_rel_path=root_rel_path,
                        code=code,
                        symbol_kind=SymbolKind.CALLABLE,
                        scope_relation=ScopeRelation.METHOD,
                        delimiter=".",
                        is_multi_prompt=is_multi_prompt,
                        is_overloaded=is_overloaded,
                    )
                )
            elif (
                (s.get("scope"))
                and not s["name"].startswith("__anon")
                and (s["kind"] in C_SHARP_CLASSES)
                or (s["kind"] in C_SHARP_DATA_STRUCTURES)
                and (s["scopeKind"] in C_SHARP_CLASSES)
            ):
                if s["scope"].split(".")[-1] in class_raw_symbol_data:
                    class_raw_symbol_data[s["scope"].split(".")[-1]].children.append(
                        create_raw_symbol_via_ctags(
                            ctags_symbol=s,
                            root_rel_path=root_rel_path,
                            code=code,
                            symbol_kind=SymbolKind.CLASS,
                            scope_relation=ScopeRelation.NESTED_CLASS,
                            delimiter=".",
                            is_multi_prompt=is_multi_prompt,
                        )
                    )
            elif (
                (s.get("scope"))
                and not s["name"].startswith("__anon")
                and (s["kind"] in C_SHARP_VARIABLES)
                and (s["scopeKind"] in C_SHARP_CLASSES)
            ):
                if s["scope"].split(".")[-1] in class_raw_symbol_data:
                    class_raw_symbol_data[s["scope"].split(".")[-1]].children.append(
                        create_raw_symbol_via_ctags(
                            ctags_symbol=s,
                            root_rel_path=root_rel_path,
                            code=code,
                            symbol_kind=SymbolKind.VARIABLE,
                            scope_relation=ScopeRelation.FIELD,
                            delimiter=".",
                            is_multi_prompt=is_multi_prompt,
                            use_padding=True,
                        )
                    )
        output = (
            None if len(class_raw_symbol_data) == 0 else cls(data=class_raw_symbol_data)
        )
        return output

    @classmethod
    def from_llm(cls, code: str, root_rel_path: str) -> Self:
        raise NotImplementedError("Static analysis should be used for C# classes")

    def to_dict(self) -> dict[str, RawSymbolData]:
        return self.data


class CsStructRawSymbolCollection(RawSymbolCollection):
    data: dict[str, RawSymbolData]

    @classmethod
    def from_static_analysis(cls, code: str, root_rel_path: Path) -> Self | None:
        is_multi_prompt = code_requires_multi_prompt(code)

        symbols = extract_symbols_w_ctags(
            root_rel_path=root_rel_path, file_content=code
        )

        global_method_counts = {}
        struct_raw_symbol_data = {}
        for s in symbols:
            if s["kind"] in C_SHARP_FUNCTIONS and not s["name"].startswith("__anon"):
                global_method_counts[s["name"]] = (
                    global_method_counts.get(s["name"], 0) + 1
                )
            if s["kind"] in C_SHARP_DATA_STRUCTURES and not s["name"].startswith(
                "__anon"
            ):
                struct_raw_symbol_data[s["name"]] = create_raw_symbol_via_ctags(
                    ctags_symbol=s,
                    root_rel_path=root_rel_path,
                    code=code,
                    symbol_kind=SymbolKind.DATA_STRUCTURE,
                    scope_relation=None,
                    delimiter=".",
                    is_multi_prompt=is_multi_prompt,
                )

        for s in symbols:
            if (
                (s.get("scope"))
                and not s["name"].startswith("__anon")
                and (s["kind"] in C_SHARP_FUNCTIONS)
                and s["scopeKind"] in C_SHARP_DATA_STRUCTURES
            ):
                # TODO: is this needed for partial case?
                # if s["scope"].split("::")[-1] not in class_raw_symbol_data:
                #     # Case where class is defined elsewhere (e.g. header), but methods for the class are defined in file
                #     class_raw_symbol_data[s["scope"].split("::")[-1]] = RawSymbolData(
                #         parser_kind=ParserKind.UCTAGS,
                #         symbol_kind=SymbolKind.DATA_STRUCTURE,
                #         name=s["scope"].split("::")[-1],
                #         path=root_rel_path,
                #         scope=None,
                #         scope_relation=None,
                #         children=[],
                #         start_line=s["line"],
                #         end_line=s["end"],
                #         symbol_code=None,
                #         file_code=None,
                #         reference_code=None,
                #         delimiter=".",
                #     )

                is_overloaded = global_method_counts[s["name"]] > 1
                struct_raw_symbol_data[s["scope"].split(".")[-1]].children.append(
                    create_raw_symbol_via_ctags(
                        ctags_symbol=s,
                        root_rel_path=root_rel_path,
                        code=code,
                        symbol_kind=SymbolKind.CALLABLE,
                        scope_relation=ScopeRelation.METHOD,
                        delimiter=".",
                        is_multi_prompt=is_multi_prompt,
                        is_overloaded=is_overloaded,
                    )
                )
            elif (
                (s.get("scope"))
                and not s["name"].startswith("__anon")
                and (s["kind"] in C_SHARP_CLASSES)
                or (s["kind"] in C_SHARP_DATA_STRUCTURES)
                and (s["scopeKind"] in C_SHARP_DATA_STRUCTURES)
            ):
                if s["scope"].split(".")[-1] in struct_raw_symbol_data:
                    struct_raw_symbol_data[s["scope"].split(".")[-1]].children.append(
                        create_raw_symbol_via_ctags(
                            ctags_symbol=s,
                            root_rel_path=root_rel_path,
                            code=code,
                            symbol_kind=SymbolKind.CLASS,
                            scope_relation=ScopeRelation.NESTED_CLASS,
                            delimiter=".",
                            is_multi_prompt=is_multi_prompt,
                        )
                    )
            elif (
                (s.get("scope"))
                and not s["name"].startswith("__anon")
                and (s["kind"] in C_SHARP_VARIABLES)
                and (s["scopeKind"] in C_SHARP_DATA_STRUCTURES)
            ):
                if s["scope"].split(".")[-1] in struct_raw_symbol_data:
                    struct_raw_symbol_data[s["scope"].split(".")[-1]].children.append(
                        create_raw_symbol_via_ctags(
                            ctags_symbol=s,
                            root_rel_path=root_rel_path,
                            code=code,
                            symbol_kind=SymbolKind.VARIABLE,
                            scope_relation=ScopeRelation.FIELD,
                            delimiter=".",
                            is_multi_prompt=is_multi_prompt,
                            use_padding=True,
                        )
                    )
        output = (
            None
            if len(struct_raw_symbol_data) == 0
            else cls(data=struct_raw_symbol_data)
        )
        return output

    @classmethod
    def from_llm(cls, code: str, root_rel_path: str) -> Self:
        raise NotImplementedError("Static analysis should be used for C# classes")

    def to_dict(self) -> dict[str, RawSymbolData]:
        return self.data


class CsInterfaceRawSymbolCollection(RawSymbolCollection):
    data: dict[str, RawSymbolData]

    @classmethod
    def from_static_analysis(cls, code: str, root_rel_path: Path) -> Self | None:
        is_multi_prompt = code_requires_multi_prompt(code)

        symbols = extract_symbols_w_ctags(
            root_rel_path=root_rel_path, file_content=code
        )

        global_method_counts = {}
        struct_raw_symbol_data = {}
        for s in symbols:
            if s["kind"] in C_SHARP_FUNCTIONS and not s["name"].startswith("__anon"):
                global_method_counts[s["name"]] = (
                    global_method_counts.get(s["name"], 0) + 1
                )
            if s["kind"] in C_SHARP_INTERFACES and not s["name"].startswith("__anon"):
                struct_raw_symbol_data[s["name"]] = create_raw_symbol_via_ctags(
                    ctags_symbol=s,
                    root_rel_path=root_rel_path,
                    code=code,
                    symbol_kind=SymbolKind.INTERFACE,
                    scope_relation=None,
                    delimiter=".",
                    is_multi_prompt=is_multi_prompt,
                )

        for s in symbols:
            if (
                (s.get("scope"))
                and not s["name"].startswith("__anon")
                and (s["kind"] in C_SHARP_FUNCTIONS)
                and s["scopeKind"] in C_SHARP_INTERFACES
            ):
                # TODO: is this needed for partial case?
                # if s["scope"].split("::")[-1] not in class_raw_symbol_data:
                #     # Case where class is defined elsewhere (e.g. header), but methods for the class are defined in file
                #     class_raw_symbol_data[s["scope"].split("::")[-1]] = RawSymbolData(
                #         parser_kind=ParserKind.UCTAGS,
                #         symbol_kind=SymbolKind.DATA_STRUCTURE,
                #         name=s["scope"].split("::")[-1],
                #         path=root_rel_path,
                #         scope=None,
                #         scope_relation=None,
                #         children=[],
                #         start_line=s["line"],
                #         end_line=s["end"],
                #         symbol_code=None,
                #         file_code=None,
                #         reference_code=None,
                #         delimiter=".",
                #     )

                is_overloaded = global_method_counts[s["name"]] > 1
                struct_raw_symbol_data[s["scope"].split(".")[-1]].children.append(
                    create_raw_symbol_via_ctags(
                        ctags_symbol=s,
                        root_rel_path=root_rel_path,
                        code=code,
                        symbol_kind=SymbolKind.CALLABLE,
                        scope_relation=ScopeRelation.METHOD,
                        delimiter=".",
                        is_multi_prompt=is_multi_prompt,
                        is_overloaded=is_overloaded,
                    )
                )
            elif (
                (s.get("scope"))
                and not s["name"].startswith("__anon")
                and (s["kind"] in C_SHARP_VARIABLES)
                and (s["scopeKind"] in C_SHARP_DATA_STRUCTURES)
            ):
                if s["scope"].split(".")[-1] in struct_raw_symbol_data:
                    struct_raw_symbol_data[s["scope"].split(".")[-1]].children.append(
                        create_raw_symbol_via_ctags(
                            ctags_symbol=s,
                            root_rel_path=root_rel_path,
                            code=code,
                            symbol_kind=SymbolKind.VARIABLE,
                            scope_relation=ScopeRelation.FIELD,
                            delimiter=".",
                            is_multi_prompt=is_multi_prompt,
                            use_padding=True,
                        )
                    )
        output = (
            None
            if len(struct_raw_symbol_data) == 0
            else cls(data=struct_raw_symbol_data)
        )
        return output

    @classmethod
    def from_llm(cls, code: str, root_rel_path: str) -> Self:
        raise NotImplementedError("Static analysis should be used for C# classes")

    def to_dict(self) -> dict[str, RawSymbolData]:
        return self.data


class CsEnumRawSymbolCollection(RawSymbolCollection):
    data: dict[str, RawSymbolData]

    @classmethod
    def from_static_analysis(cls, code: str, root_rel_path: Path) -> Self | None:
        is_multi_prompt = code_requires_multi_prompt(code)

        symbols = extract_symbols_w_ctags(
            root_rel_path=root_rel_path, file_content=code
        )

        enum_raw_symbol_data = {}
        for s in symbols:
            if s["kind"] in C_SHARP_ENUMS and not s["name"].startswith("__anon"):
                enum_raw_symbol_data[s["name"]] = create_raw_symbol_via_ctags(
                    ctags_symbol=s,
                    root_rel_path=root_rel_path,
                    code=code,
                    symbol_kind=SymbolKind.DATA_STRUCTURE,
                    scope_relation=None,
                    delimiter=".",
                    is_multi_prompt=is_multi_prompt,
                )

        for s in sorted(symbols, key=lambda d: d["line"]):
            if (
                (s.get("scope"))
                and not s["name"].startswith("__anon")
                and (s["kind"] in C_SHARP_ENUM_VALS)
                and s["scopeKind"] in C_SHARP_ENUMS
            ):
                # TODO: is this needed for partial case?
                enum_raw_symbol_data[s["scope"].split(".")[-1]].children.append(
                    create_raw_symbol_via_ctags(
                        ctags_symbol=s,
                        root_rel_path=root_rel_path,
                        code=code,
                        symbol_kind=SymbolKind.VARIABLE,
                        scope_relation=ScopeRelation.ENUMERATOR,
                        delimiter=".",
                        is_multi_prompt=is_multi_prompt,
                    )
                )
        output = (
            None if len(enum_raw_symbol_data) == 0 else cls(data=enum_raw_symbol_data)
        )
        return output

    @classmethod
    def from_llm(cls, code: str, root_rel_path: str) -> Self:
        raise NotImplementedError("Static analysis should be used for C# enums")

    def to_dict(self) -> dict[str, RawSymbolData]:
        return self.data


# Template interface functions
class_dict_from_llm_cs = partial(
    CsClassCollection.dict_from_llm,
    CsClassData,
)

struct_dict_from_llm_cs = partial(
    CsStructCollection.dict_from_llm,
    CsStructData,
)

interface_dict_from_llm_cs = partial(
    CsInterfaceCollection.dict_from_llm,
    CsInterfaceData,
)

enum_dict_from_llm_cs = partial(
    CsEnumCollection.dict_from_llm,
    CsEnumData,
)
