from pathlib import Path
from typing import Self

from pydantic import PrivateAttr
from utils.models import ChatOpenAI
from utils.symbol_table.utils import get_fully_qualified_name

from .ir_common import (
    FieldNameWithRawContent,
    IrCollection,
    IrData,
    ListedBacktickNameRawContentWithNone,
    ListedCommaCombinedBackTickRawContentNoNone,
    ListedRawContentNoNone,
    ListedRawContentWithNone,
    RawContent,
)
from .symbol_common import (
    RawSymbolCollection,
    RawSymbolData,
    ReifiedSymbol,
    ScopeRelation,
    SymbolKind,
    code_requires_multi_prompt,
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
    def default_instance(cls, reified_symbol: ReifiedSymbol | None = None) -> Self:
        return cls(description=FieldNameWithRawContent(content=""))


class CsMethodData(IrData):
    single_sentence: RawContent
    _type: ListedCommaCombinedBackTickRawContentNoNone = PrivateAttr(
        default=ListedCommaCombinedBackTickRawContentNoNone(content=[])
    )
    _modifiers: ListedCommaCombinedBackTickRawContentNoNone = PrivateAttr(
        default=ListedCommaCombinedBackTickRawContentNoNone(content=[])
    )
    inputs: ListedBacktickNameRawContentWithNone
    control_flow: ListedRawContentWithNone
    output: FieldNameWithRawContent

    def _apply_bespoke_data(self) -> None:
        modifiers = []

        for modifier in self._reified_symbol.raw.bespoke_data.modifiers:
            modifiers.append(modifier)
        self._modifiers.content = modifiers
        self._type.content = [
            self._reified_symbol.raw.bespoke_data.kind.replace("_", " ")
        ]

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

    @classmethod
    def default_instance(cls, reified_symbol: ReifiedSymbol | None = None) -> Self:
        return cls(
            single_sentence=RawContent(content=""),
            inputs=ListedBacktickNameRawContentWithNone(content=[]),
            control_flow=ListedBacktickNameRawContentWithNone(content=[]),
            output=FieldNameWithRawContent(content=""),
        )


class CsStructData(IrData):
    _type: ListedCommaCombinedBackTickRawContentNoNone = PrivateAttr(
        default=ListedCommaCombinedBackTickRawContentNoNone(content=[])
    )
    _modifiers: ListedCommaCombinedBackTickRawContentNoNone = PrivateAttr(
        default=ListedCommaCombinedBackTickRawContentNoNone(content=[])
    )
    _partial_implementations: ListedRawContentNoNone = PrivateAttr(
        default=ListedRawContentNoNone(content=[])
    )
    description: FieldNameWithRawContent
    _supported_child_ordering: list[str] = PrivateAttr(
        default=[
            ScopeRelation.FIELD,
            ScopeRelation.METHOD,
            ScopeRelation.NESTED_CLASS,
        ]
    )

    def _apply_bespoke_data(self) -> None:
        partial_implementations = []
        modifiers = []

        for child in self._reified_symbol.children:
            if child.raw.symbol_kind == SymbolKind.CLASS:
                path_part = child.raw.file_path
                kind_part = child.raw.symbol_kind.name.lower()
                fqn = get_fully_qualified_name(child.raw)
                partial_implementations.append(
                    f"[`{path_part}`](<{path_part}#{kind_part}:{fqn}>)"
                )

        for modifier in self._reified_symbol.raw.bespoke_data.modifiers:
            modifiers.append(modifier)
        self._partial_implementations.content = partial_implementations
        self._modifiers.content = modifiers
        self._type.content = [
            self._reified_symbol.raw.bespoke_data.kind.replace("_", " ")
        ]

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
    def default_instance(cls, reified_symbol: ReifiedSymbol | None = None) -> Self:
        return cls(
            description=FieldNameWithRawContent(content=""),
            implements=ListedRawContentNoNone(content=[]),
            modifiers=ListedRawContentNoNone(content=[]),
        )


class CsStructCollection(IrCollection):
    data: dict[str, CsStructData | list[CsStructData]]

    @classmethod
    def from_llm(cls, llm: ChatOpenAI, symbols_list: RawSymbolCollection) -> Self:
        return cls.from_llm_with_ir_data(CsStructData, llm, symbols_list)


class CsClassData(IrData):
    _type: ListedCommaCombinedBackTickRawContentNoNone = PrivateAttr(
        default=ListedCommaCombinedBackTickRawContentNoNone(content=[])
    )
    _modifiers: ListedCommaCombinedBackTickRawContentNoNone = PrivateAttr(
        default=ListedCommaCombinedBackTickRawContentNoNone(content=[])
    )
    _partial_implementations: ListedRawContentNoNone = PrivateAttr(
        default=ListedRawContentNoNone(content=[])
    )
    description: FieldNameWithRawContent
    _supported_child_ordering: list[str] = PrivateAttr(
        default=[
            ScopeRelation.FIELD,
            ScopeRelation.METHOD,
            ScopeRelation.NESTED_CLASS,
        ]
    )

    def _apply_bespoke_data(self) -> None:
        partial_implementations = []
        modifiers = []

        for child in self._reified_symbol.children:
            if child.raw.symbol_kind == SymbolKind.CLASS:
                path_part = child.raw.file_path
                kind_part = child.raw.symbol_kind.name.lower()
                fqn = get_fully_qualified_name(child.raw)
                partial_implementations.append(
                    f"[`{path_part}`](<{path_part}#{kind_part}:{fqn}>)"
                )

        for modifier in self._reified_symbol.raw.bespoke_data.modifiers:
            modifiers.append(modifier)
        self._partial_implementations.content = partial_implementations
        self._modifiers.content = modifiers
        kind = (
            "class"
            if self._reified_symbol.raw.bespoke_data.kind == "standard"
            else self._reified_symbol.raw.bespoke_data.kind
        )
        self._type.content = [kind]

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
    def default_instance(cls, reified_symbol: ReifiedSymbol | None = None) -> Self:
        return cls(
            description=FieldNameWithRawContent(content=""),
            inherits_from=ListedRawContentNoNone(content=[]),
            implements=ListedRawContentNoNone(content=[]),
            modifiers=ListedRawContentNoNone(content=[]),
        )


class CsClassCollection(IrCollection):
    data: dict[str, CsClassData | list[CsClassData]]

    @classmethod
    def from_llm(cls, llm: ChatOpenAI, symbols_list: RawSymbolCollection) -> Self:
        return cls.from_llm_with_ir_data(CsClassData, llm, symbols_list)


class CsInterfaceData(IrData):
    _modifiers: ListedCommaCombinedBackTickRawContentNoNone = PrivateAttr(
        default=ListedCommaCombinedBackTickRawContentNoNone(content=[])
    )
    _partial_implementations: ListedRawContentNoNone = PrivateAttr(
        default=ListedRawContentNoNone(content=[])
    )
    description: FieldNameWithRawContent
    _supported_child_ordering: list[str] = PrivateAttr(
        default=[
            ScopeRelation.FIELD,
            ScopeRelation.METHOD,
        ]
    )

    def _apply_bespoke_data(self) -> None:
        partial_implementations = []
        modifiers = []

        for child in self._reified_symbol.children:
            if child.raw.symbol_kind == SymbolKind.CLASS:
                path_part = child.raw.file_path
                kind_part = child.raw.symbol_kind.name.lower()
                fqn = get_fully_qualified_name(child.raw)
                partial_implementations.append(
                    f"[`{path_part}`](<{path_part}#{kind_part}:{fqn}>)"
                )

        for modifier in self._reified_symbol.raw.bespoke_data.modifiers:
            modifiers.append(modifier)
        self._partial_implementations.content = partial_implementations
        self._modifiers.content = modifiers

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
    def default_instance(cls, reified_symbol: ReifiedSymbol | None = None) -> Self:
        return cls(
            interfaces_inherited=ListedRawContentNoNone(content=[]),
            description=FieldNameWithRawContent(content=""),
        )


class CsInterfaceCollection(IrCollection):
    data: dict[str, CsInterfaceData | list[CsInterfaceData]]

    @classmethod
    def from_llm(cls, llm: ChatOpenAI, symbols_list: RawSymbolCollection) -> Self:
        return cls.from_llm_with_ir_data(CsInterfaceData, llm, symbols_list)


# Symbol Extraction Classes
class CsClassRawSymbolCollection(RawSymbolCollection):
    data: dict[str, RawSymbolData]

    @classmethod
    def from_static_analysis(
        cls, code: str, root_rel_path: Path, reified_symbols: list[ReifiedSymbol]
    ) -> Self | None:
        class_symbols = [
            sym
            for sym in reified_symbols
            if sym.raw.symbol_kind == SymbolKind.CLASS and sym.is_definition
        ]
        class_raw_symbol_data = {}
        is_large_file = code_requires_multi_prompt(code)

        global_method_counts = {}
        fn_symbols = [
            sym
            for sym in reified_symbols
            if sym.raw.symbol_kind == SymbolKind.CALLABLE and sym.is_definition
        ]
        for fn_symbol in fn_symbols:
            if (
                fn_symbol.raw.name is not None
                and fn_symbol.raw.name not in global_method_counts
            ):
                global_method_counts[fn_symbol.raw.name] = 0
            global_method_counts[fn_symbol.raw.name] += 1

        for class_symbol in class_symbols:
            if (
                class_symbol.raw.name is not None
                and class_symbol.raw.name not in class_raw_symbol_data
            ):
                # Do this check in case multiple partials of the same class are present in the same file
                raw_symbol_data = RawSymbolData.from_tree_sitter_raw_symbol(
                    ts_symbol=class_symbol.raw,
                    path=root_rel_path,
                    scope=None,
                    scope_relation=None,
                    children=[],
                    reference_code=None,
                    delimiter=".",
                    is_large_file=is_large_file,
                    is_overloaded=False,
                    use_padding=False,
                    code=code,
                    reified_symbol=class_symbol,
                )
                class_raw_symbol_data[class_symbol.raw.name] = raw_symbol_data
            for child in class_symbol.children:
                if (
                    child.raw.symbol_kind == SymbolKind.CALLABLE
                    and child.raw.file_path
                    == class_symbol.raw.file_path  # NOTE: we do this for partial classes, we only document methods that are in the file of THIS partial
                ):
                    is_overloaded = global_method_counts[child.raw.name] > 1
                    class_raw_symbol_data[class_symbol.raw.name].children.append(
                        RawSymbolData.from_tree_sitter_raw_symbol(
                            ts_symbol=child.raw,
                            path=root_rel_path,
                            scope=class_symbol.raw.name,
                            scope_relation=ScopeRelation.METHOD,
                            children=[],
                            reference_code=None,
                            delimiter=".",
                            is_large_file=is_large_file,
                            is_overloaded=is_overloaded,
                            use_padding=False,
                            code=code,
                            reified_symbol=child,
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
    def from_static_analysis(
        cls, code: str, root_rel_path: Path, reified_symbols: list[ReifiedSymbol]
    ) -> Self | None:
        ds_symbols = [
            sym
            for sym in reified_symbols
            if sym.raw.symbol_kind == SymbolKind.DATA_STRUCTURE and sym.is_definition
        ]
        ds_raw_symbol_data = {}
        is_large_file = code_requires_multi_prompt(code)

        global_method_counts = {}
        fn_symbols = [
            sym
            for sym in reified_symbols
            if sym.raw.symbol_kind == SymbolKind.CALLABLE and sym.is_definition
        ]
        for fn_symbol in fn_symbols:
            if (
                fn_symbol.raw.name is not None
                and fn_symbol.raw.name not in global_method_counts
            ):
                global_method_counts[fn_symbol.raw.name] = 0
            global_method_counts[fn_symbol.raw.name] += 1

        for ds_symbol in ds_symbols:
            if (
                ds_symbol.raw.name is not None
                and ds_symbol.raw.name not in ds_raw_symbol_data
            ):
                # Do this check in case multiple partials of the same class are present in the same file
                raw_symbol_data = RawSymbolData.from_tree_sitter_raw_symbol(
                    ts_symbol=ds_symbol.raw,
                    path=root_rel_path,
                    scope=None,
                    scope_relation=None,
                    children=[],
                    reference_code=None,
                    delimiter=".",
                    is_large_file=is_large_file,
                    is_overloaded=False,
                    use_padding=False,
                    code=code,
                    reified_symbol=ds_symbol,
                )
                ds_raw_symbol_data[ds_symbol.raw.name] = raw_symbol_data
            for child in ds_symbol.children:
                if (
                    child.raw.symbol_kind == SymbolKind.CALLABLE
                    and child.raw.file_path
                    == ds_symbol.raw.file_path  # NOTE: we do this for partial classes, we only document methods that are in the file of THIS partial
                ):
                    is_overloaded = global_method_counts[child.raw.name] > 1
                    ds_raw_symbol_data[ds_symbol.raw.name].children.append(
                        RawSymbolData.from_tree_sitter_raw_symbol(
                            ts_symbol=child.raw,
                            path=root_rel_path,
                            scope=ds_symbol.raw.name,
                            scope_relation=ScopeRelation.METHOD,
                            children=[],
                            reference_code=None,
                            delimiter=".",
                            is_large_file=is_large_file,
                            is_overloaded=is_overloaded,
                            use_padding=False,
                            code=code,
                            reified_symbol=child,
                        )
                    )
        output = None if len(ds_raw_symbol_data) == 0 else cls(data=ds_raw_symbol_data)
        return output

    @classmethod
    def from_llm(cls, code: str, root_rel_path: str) -> Self:
        raise NotImplementedError("Static analysis should be used for C# classes")

    def to_dict(self) -> dict[str, RawSymbolData]:
        return self.data


class CsInterfaceRawSymbolCollection(RawSymbolCollection):
    data: dict[str, RawSymbolData]

    @classmethod
    def from_static_analysis(
        cls, code: str, root_rel_path: Path, reified_symbols: list[ReifiedSymbol]
    ) -> Self | None:
        interface_symbols = [
            sym
            for sym in reified_symbols
            if sym.raw.symbol_kind == SymbolKind.INTERFACE and sym.is_definition
        ]
        interface_raw_symbol_data = {}
        is_large_file = code_requires_multi_prompt(code)

        global_method_counts = {}
        fn_symbols = [
            sym
            for sym in reified_symbols
            if sym.raw.symbol_kind == SymbolKind.CALLABLE and sym.is_definition
        ]
        for fn_symbol in fn_symbols:
            if (
                fn_symbol.raw.name is not None
                and fn_symbol.raw.name not in global_method_counts
            ):
                global_method_counts[fn_symbol.raw.name] = 0
            global_method_counts[fn_symbol.raw.name] += 1

        for interface_symbol in interface_symbols:
            if (
                interface_symbol.raw.name is not None
                and interface_symbol.raw.name not in interface_raw_symbol_data
            ):
                # Do this check in case multiple partials of the same class are present in the same file
                raw_symbol_data = RawSymbolData.from_tree_sitter_raw_symbol(
                    ts_symbol=interface_symbol.raw,
                    path=root_rel_path,
                    scope=None,
                    scope_relation=None,
                    children=[],
                    reference_code=None,
                    delimiter=".",
                    is_large_file=is_large_file,
                    is_overloaded=False,
                    use_padding=False,
                    code=code,
                    reified_symbol=interface_symbol,
                )
                interface_raw_symbol_data[interface_symbol.raw.name] = raw_symbol_data
            for child in interface_symbol.children:
                if (
                    child.raw.symbol_kind == SymbolKind.CALLABLE
                    and child.raw.file_path
                    == interface_symbol.raw.file_path  # NOTE: we do this for partial classes, we only document methods that are in the file of THIS partial
                ):
                    is_overloaded = global_method_counts[child.raw.name] > 1
                    interface_raw_symbol_data[
                        interface_symbol.raw.name
                    ].children.append(
                        RawSymbolData.from_tree_sitter_raw_symbol(
                            ts_symbol=child.raw,
                            path=root_rel_path,
                            scope=interface_symbol.raw.name,
                            scope_relation=ScopeRelation.METHOD,
                            children=[],
                            reference_code=None,
                            delimiter=".",
                            is_large_file=is_large_file,
                            is_overloaded=is_overloaded,
                            use_padding=False,
                            code=code,
                            reified_symbol=child,
                        )
                    )
        output = (
            None
            if len(interface_raw_symbol_data) == 0
            else cls(data=interface_raw_symbol_data)
        )
        return output

    @classmethod
    def from_llm(cls, code: str, root_rel_path: str) -> Self:
        raise NotImplementedError("Static analysis should be used for C# classes")

    def to_dict(self) -> dict[str, RawSymbolData]:
        return self.data


# Covered by data structures?
# class CsEnumRawSymbolCollection(RawSymbolCollection):
#     data: dict[str, RawSymbolData]
#
#     @classmethod
#     def from_static_analysis(cls, code: str, root_rel_path: Path) -> Self | None:
#         is_multi_prompt = code_requires_multi_prompt(code)
#
#         symbols = extract_symbols_w_ctags(
#             root_rel_path=root_rel_path, file_content=code
#         )
#
#         enum_raw_symbol_data = {}
#         for s in symbols:
#             if s["kind"] in C_SHARP_ENUMS and not s["name"].startswith("__anon"):
#                 enum_raw_symbol_data[s["name"]] = create_raw_symbol_via_ctags(
#                     ctags_symbol=s,
#                     root_rel_path=root_rel_path,
#                     code=code,
#                     symbol_kind=SymbolKind.DATA_STRUCTURE,
#                     scope_relation=None,
#                     delimiter=".",
#                     is_multi_prompt=is_multi_prompt,
#                 )
#
#         for s in sorted(symbols, key=lambda d: d["line"]):
#             if (
#                 (s.get("scope"))
#                 and not s["name"].startswith("__anon")
#                 and (s["kind"] in C_SHARP_ENUM_VALS)
#                 and s["scopeKind"] in C_SHARP_ENUMS
#             ):
#                 # TODO: is this needed for partial case?
#                 enum_raw_symbol_data[s["scope"].split(".")[-1]].children.append(
#                     create_raw_symbol_via_ctags(
#                         ctags_symbol=s,
#                         root_rel_path=root_rel_path,
#                         code=code,
#                         symbol_kind=SymbolKind.VARIABLE,
#                         scope_relation=ScopeRelation.ENUMERATOR,
#                         delimiter=".",
#                         is_multi_prompt=is_multi_prompt,
#                     )
#                 )
#         output = (
#             None if len(enum_raw_symbol_data) == 0 else cls(data=enum_raw_symbol_data)
#         )
#         return output
#
#     @classmethod
#     def from_llm(cls, code: str, root_rel_path: str) -> Self:
#         raise NotImplementedError("Static analysis should be used for C# enums")
#
#     def to_dict(self) -> dict[str, RawSymbolData]:
#         return self.data
#
