from pathlib import Path
from typing import Self

from pydantic import PrivateAttr
from shared.prompts.structured_prompting import (
    GENERAL_STE_STYLE_INSTRUCTION,
    NO_RESTATEMENT_STYLE_INSTRUCTION_FOR_SYMBOLS,
    USE_BACKTICKS_STYLE_INSTRUCTION,
    Component,
    Prompt,
)
from utils.models import ChatOpenAI
from utils.treesitter_drivers.go_driver import GoDriverTree

from .ir_common import (
    FieldNameTypedWithRawContent,
    FieldNameWithBackTickContent,
    FieldNameWithRawContent,
    FourHeaderNamedContentNoNone,
    IrCollection,
    IrData,
    ListedBacktickNameRawContentNoNone,
    ListedBacktickNameTypeRawContentNoNone,
    ListedBacktickNameTypeRawContentWithNone,
    ListedRawContentWithNone,
    RawContent,
    RawContentNoNone,
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

# System prompts for Go documentation
SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_GO = """
You are an expert Go programmer and a software engineering documentation expert. You write detailed documentation to explain code written in Go.

You are skilled at explaining technical details as well as recognizing and articulating the key conceptual components and purpose of software.
"""

SOURCE_CODE_SMALL_SYSTEM_PROMPT_GENERAL_GO = """
You are an expert Go programmer and a software engineering documentation expert. You write detailed documentation to explain code written in Go.

You are skilled at explaining technical details as well as recognizing and articulating the key conceptual components and purpose of software.

You specialize in effectively describing small and short source code files. Your goal is to be terse and clear, since the source code you are describing is small and simple.
"""

# User prompts for file purpose analysis
SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT = """
You will be given the content of a source code file. In 1 or 2 paragraphs, explain the purpose of the file.

When writing your paragraphs, do not use speculative language.

When writing your paragraphs, consider questions like the following. You do not need to explicitly state these ideas, they are just given as examples of the kind of information to provide:

- Does this code provide narrow or broad functionality?
- What are the most important technical components?
- Is this code a collection of many different components? If so, what is the common theme or purpose?
- What kind of code is this? For example, is this a package with exported APIs, a command-line application, a test file, etc.?
- Does it define public APIs or external interfaces?
- Are there any Go-specific patterns like goroutines, channels, or interfaces being used?
"""

SOURCE_CODE_SMALL_PURPOSE_USER_PROMPT = """
You will be given the content of a source code file. In a single paragraph of 3 to 5 sentences, explain the purpose of the file.

Consider questions such as the following when providing your output:

- Does this code provide narrow or broad functionality?
- What kind of code is this? For example, is this a simple utility package, a main program entry point, test code, etc.?
- Are any Go-specific idioms or patterns being used?
"""

TECHNICAL_CONCEPTS = """
You will be given the content of a source code file. In a single paragraph of 3 to 5 sentences, describe the important technical features and their interactions in the file.

In writing your description, write about the conceptual use cases, applications, logic, and component interactions instead of focusing on particular structs, functions, variables, etc. Consider Go-specific concepts like goroutines, channels, interfaces, and error handling patterns.
"""

# JSON schema prompts for data structures
DATA_STRUCTURES_FOUND_SYSTEM_PROMPT_JSON = """
You are an expert Go programmer and a software engineering documentation expert. You write detailed documentation to explain code written in Go.

You focus on writing technical documentation for data structures in Go. You are skilled at explaining technical details as well as recognizing and articulating the key conceptual components and purpose of software.

You will be given the name of a data structure to document and the source code where the data structure is defined.

There are 3 data structure types we are documenting:
- `struct`: A type composed of collection of orthogonal fields.
- `new_type`: A new type with distinct semantics.
- `type_alias`: A simple alias for an existing type with no distinct semantics.

`new_type` and `type_alias`es are superficially similar but have different semantics that are important. Do not confuse them or terms related to them in your descriptions. For example, do not describe a new_type as "an alias" -- reserve that kind of description for `type_alias`. Also, do not comment on the relative function or value of a new type or a type alias, just make sure you refer to them correctly in your descriptions.

Your job is to describe the data structure. **Always respond using exactly the following JSON schema**:
{
    "fields": [
        {"name": <field_name1>, "type": <type>, "content": <Terse 1 sentence description of the first struct field>},
        {"name": <field_name2>, "type": <type>, "content": <Terse 1 sentence description of the second struct field>},
        ...
    ],
    "description": <one paragraph description of the data structure>,
}

Return JSON according to the schema above. Do not use the format ```json ... ```, just return the JSON data.
"""

DATA_STRUCTURES_FOUND_USER_PROMPT = """
Summarize the data structure in the code provided below.

- When describing a data structure, provide detail that matches the complexity of the data structure. Large and complex data structures with many fields should get longer explanations, while small ones need only a single sentence.
- For empty structs, explain their purpose (often used as markers or for method receivers).
- For type aliases, explain how the alias improves code readability or provides domain-specific naming.

Data structure to document:
"""

# JSON schema prompts for functions and methods
CALLABLES_FOUND_SYSTEM_PROMPT_JSON = """
You are an expert Go programmer and a software engineering documentation expert. You write detailed documentation to explain code written in Go.

You focus on writing technical documentation for free functions. You are skilled at explaining technical details as well as recognizing and articulating the key conceptual components and purpose of software.

You will be given the name of a function to document and the source code where it is defined.

Your job is to describe the function. **Always respond using exactly the following JSON schema**:
{
    "single_sentence": <terse single sentence description of the function>,
    "inputs": [
        {"name": <input_arg1>, "type": <type of the input>, "content": <description of input argument 1, do not restate the type>},
        {"name": <input_arg2>, "type": <type of the input>, "content": <description of input argument 2, do not restate the type>},
        ...
    ],
    "logic_and_control_flow": [
        <bullet point 1 for description of control flow>,
        <bullet point 2 for description of control flow>,
        ...
    ],
    "output": <description of output, including error returns>,
}

Return JSON according to the schema above. Do not use the format ```json ... ```, just return the JSON data.
"""

CALLABLES_FOUND_USER_PROMPT = """
Summarize the function in the code provided below. Describe the inputs, control flow and logic, and outputs.

- When describing a function, provide detail that matches the complexity of the implementation. Large and complex functions should get longer explanations.
- Pay attention to Go idioms like error handling, defer statements, and goroutine usage.

Function to document:
"""

METHODS_FOUND_SYSTEM_PROMPT_JSON = """
You are an expert Go programmer and a software engineering documentation expert. You write detailed documentation to explain code written in Go.

You focus on writing technical documentation for methods. You are skilled at explaining technical details as well as recognizing and articulating the key conceptual components and purpose of software.

You will be given the name of a method to document and the source code where it is defined.

Your job is to describe the function or method. **Always respond using exactly the following JSON schema**:
{
    "single_sentence": <terse single sentence description of the function>,
    "inputs": [
        {"name": <input_arg1>, "type": <type of the input>, "content": <description of input argument 1, do not restate the type>},
        {"name": <input_arg2>, "type": <type of the input>, "content": <description of input argument 2, do not restate the type>},
        ...
    ],
    "logic_and_control_flow": [
        <bullet point 1 for description of control flow>,
        <bullet point 2 for description of control flow>,
        ...
    ],
    "output": <description of output, including error returns>,
}
For method inputs, do not include the receiver type as an input argument (what's contained in the first set of parentheses in the method signature). Only describe the explicit input parameters in the second set of parentheses in the function signature.

Return JSON according to the schema above. Do not use the format ```json ... ```, just return the JSON data.
"""

METHODS_FOUND_USER_PROMPT = """
Summarize the method in the code provided below. Describe the inputs, control flow and logic, and outputs.

- When describing a method, provide detail that matches the complexity of the implementation. Large and complex functions should get longer explanations.
- Pay attention to Go idioms like error handling, defer statements, and goroutine usage.
- For methods, explain how the method modifies or uses the receiver.

Function/Method to document:
"""

# JSON schema prompts for interfaces
INTERFACES_FOUND_SYSTEM_PROMPT_JSON = """
You are an expert Go programmer and a software engineering documentation expert. You write detailed documentation to explain code written in Go.

You focus on writing technical documentation for interfaces in Go. You are skilled at explaining technical details as well as recognizing and articulating the key conceptual components and purpose of software.

You will be given the name of an interface to document and the source code where the interface is defined.

Your job is to describe the interface. **Always respond using exactly the following JSON schema**:
{
    "description": <one paragraph description of the interface and its contract>,
    "methods": [
        {"name": <method_name1>, "signature": <full method signature>, "content": <Terse description of what this method should do>},
        {"name": <method_name2>, "signature": <full method signature>, "content": <Terse description of what this method should do>},
        ...
    ],
}

Return JSON according to the schema above. Do not use the format ```json ... ```, just return the JSON data.
"""

INTERFACES_FOUND_USER_PROMPT = """
Summarize the interface in the code provided below.

- Describe the contract that implementers must fulfill.
- Explain the purpose and typical usage of the interface.
- If the interface embeds other interfaces, explain the relationship.
- For empty interfaces (interface{}), explain their purpose as universal types.

Interface to document:
"""

# JSON schema prompts for variables and constants
VARIABLES_FOUND_SYSTEM_PROMPT_JSON = """
You are an expert Go programmer and a software engineering documentation expert. You write detailed documentation to explain code written in Go.

You focus on writing technical documentation for package-level variables and constants in Go. You are skilled at explaining technical details as well as recognizing and articulating the key conceptual components and purpose of software.

You will be given variable or constant declarations to document and the source code where they are defined.

Your job is to describe the variable or constant. **Always respond using exactly the following JSON schema**:
{
    "type": the type of the global variable or constant (e.g., int, string, the name of a custom struct type, etc.),
    "description": <one paragraph description of the variable/constant or group>,
}

Return JSON according to the schema above. Do not use the format ```json ... ```, just return the JSON data.
"""

VARIABLE_GROUPS_FOUND_SYSTEM_PROMPT_JSON = """
You are an expert Go programmer and a software engineering documentation expert. You write detailed documentation to explain code written in Go.

You focus on writing technical documentation for package-level variable and constant groups in Go. You are skilled at explaining technical details as well as recognizing and articulating the key conceptual components and purpose of software.

You will be given variable or constant group declarations to document and the source code where they are defined.

Your job is to describe the variable or constant. **Always respond using exactly the following JSON schema**:
{
    "items": [
        {"name": <var_or_const_name1>, "value": <initial value if visible>, "content": <Terse description>},
        {"name": <var_or_const_name2>, "value": <initial value if visible>, "content": <Terse description>},
        ...
    ],
    "kind": <"variable_group", or "constant_group">,
    "description": <one paragraph description of the variable/constant group>,
}

Return JSON according to the schema above. Do not use the format ```json ... ```, just return the JSON data.
"""

VARIABLES_FOUND_USER_PROMPT = """
Summarize the variable or constant declaration in the code provided below.

This is a single variable, do not describe more than one variable, it is not part of a group.

Variable/Constant to document:
"""

VARIABLE_GROUPS_FOUND_USER_PROMPT = """
Summarize the variable or constant declaration in the code provided below.

- For constants using iota, explain the enumeration pattern.
- For variable/constant groups, explain their collective purpose.
- Note whether these are configuration values, enumeration constants, or other patterns.

Variable/Constant Group to document:
"""


# RawSymbolCollection Classes for Tree-Sitter parsed symbols


class GoImportRawSymbolCollection(RawSymbolCollection):
    data: dict[str, RawSymbolData]

    @classmethod
    def from_static_analysis(cls, code: str, root_rel_path: Path) -> Self | None:
        driver_tree = GoDriverTree.from_code(code, root_rel_path)
        is_large_file = code_requires_multi_prompt(code)
        import_symbols = driver_tree.extract_imports()

        import_dict = {}
        for ts_symbol in import_symbols:
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
        instance = cls(data=import_dict)
        return instance

    @classmethod
    def from_llm(cls, code: str, root_rel_path: str) -> Self:
        raise NotImplementedError("Static analysis should be used for Go imports")

    def to_dict(self) -> dict[str, RawSymbolData]:
        return self.data


# IrData Classes for LLM-based symbol analysis


class GoMethodData(IrData):
    single_sentence: RawContent
    _type_parameters: RawContentNoNone = PrivateAttr(
        default=RawContentNoNone(content="")
    )
    inputs: ListedBacktickNameTypeRawContentWithNone
    logic_and_control_flow: ListedRawContentWithNone
    output: FieldNameTypedWithRawContent

    def _apply_bespoke_data(self) -> None:
        self._type_parameters = RawContentNoNone(
            content=self._reified_symbol.raw.bespoke_data.ty_params
        )

    @classmethod
    def default_instance(cls, reified_symbol: ReifiedSymbol | None = None) -> Self:
        return cls(
            single_sentence=RawContent(content=""),
            inputs=ListedBacktickNameTypeRawContentNoNone(content=[]),
            logic_and_control_flow=ListedRawContentWithNone(content=[]),
            output=FieldNameTypedWithRawContent(type="", content=""),
        )

    @classmethod
    def system_prompt(cls, symbol: RawSymbolData) -> str:
        return (
            Prompt.empty()
            .append(Component(string=METHODS_FOUND_SYSTEM_PROMPT_JSON))
            .append(GENERAL_STE_STYLE_INSTRUCTION)
            .append(USE_BACKTICKS_STYLE_INSTRUCTION)
            .into_str()
        )

    @classmethod
    def user_prompt(cls, symbol: RawSymbolData) -> str:
        user_prompt = (
            Prompt.empty()
            .append(NO_RESTATEMENT_STYLE_INSTRUCTION_FOR_SYMBOLS)
            .append(
                Component(
                    string=f"{METHODS_FOUND_USER_PROMPT}{symbol.name}\n\nFunction/Method Code:\n\n{symbol.symbol_code}"
                )
            )
        )
        if symbol.file_code:
            user_prompt.append(
                Component(string=f"\n\nFull File Code:\n\n{symbol.file_code}")
            )
        return user_prompt.into_str()

    @classmethod
    def child_to_ir(cls, symbol: RawSymbolData) -> type[IrData] | None:
        return None  # Go callables don't have children in our model

    @classmethod
    def child_to_field_name(cls, child: RawSymbolData) -> str:
        raise NotImplementedError("Callables should not have children")


class GoDataStructureData(IrData):
    _type: FieldNameWithBackTickContent = PrivateAttr(
        default=FieldNameWithBackTickContent(content="")
    )
    fields: ListedBacktickNameTypeRawContentNoNone
    description: FieldNameWithRawContent
    _supported_child_ordering: list[str] = PrivateAttr(default=[ScopeRelation.METHOD])

    def _apply_bespoke_data(self) -> None:
        self._type = FieldNameWithBackTickContent(
            content=self._reified_symbol.raw.bespoke_data.kind
        )

    @classmethod
    def default_instance(cls, reified_symbol: ReifiedSymbol | None = None) -> Self:
        return cls(
            fields=ListedBacktickNameTypeRawContentNoNone(content=[]),
            description=FieldNameWithRawContent(field_name="Description", content=""),
        )

    @classmethod
    def system_prompt(cls, symbol: RawSymbolData) -> str:
        return (
            Prompt.empty()
            .append(Component(string=DATA_STRUCTURES_FOUND_SYSTEM_PROMPT_JSON))
            .append(GENERAL_STE_STYLE_INSTRUCTION)
            .append(USE_BACKTICKS_STYLE_INSTRUCTION)
            .into_str()
        )

    @classmethod
    def user_prompt(cls, symbol: RawSymbolData) -> str:
        user_prompt = (
            Prompt.empty()
            .append(NO_RESTATEMENT_STYLE_INSTRUCTION_FOR_SYMBOLS)
            .append(
                Component(
                    string=f"{DATA_STRUCTURES_FOUND_USER_PROMPT}{symbol.name}\n\nType Definition:\n\n{symbol.symbol_code}"
                )
            )
        )
        if symbol.file_code:
            user_prompt.append(
                Component(string=f"\n\nFull File Code:\n\n{symbol.file_code}")
            )
        ds_type = symbol.reified_symbol.raw.bespoke_data.kind
        user_prompt.append(
            Component(
                string=f"\n\nNote: This is a {ds_type}. Describe it as such in the description."
            )
        )
        return user_prompt.into_str()

    @classmethod
    def child_to_ir(cls, symbol: RawSymbolData) -> type[IrData] | None:
        mapping = {
            SymbolKind.CALLABLE: GoMethodData,
        }
        return mapping.get(symbol.symbol_kind)

    @classmethod
    def child_to_field_name(cls, child: RawSymbolData) -> str:
        mapping = {
            SymbolKind.CALLABLE: ScopeRelation.METHOD,
        }
        return mapping.get(child.symbol_kind)


class GoCallableData(IrData):
    single_sentence: RawContent
    inputs: ListedBacktickNameTypeRawContentWithNone
    logic_and_control_flow: ListedRawContentWithNone
    output: FieldNameTypedWithRawContent

    def _apply_bespoke_data(self) -> None:
        self._type_parameters = RawContentNoNone(
            content=self._reified_symbol.raw.bespoke_data.ty_params
        )

    @classmethod
    def default_instance(cls, reified_symbol: ReifiedSymbol | None = None) -> Self:
        return cls(
            single_sentence=RawContent(content=""),
            inputs=ListedBacktickNameTypeRawContentNoNone(content=[]),
            logic_and_control_flow=ListedRawContentWithNone(content=[]),
            output=FieldNameTypedWithRawContent(type="", content=""),
        )

    @classmethod
    def system_prompt(cls, symbol: RawSymbolData) -> str:
        return (
            Prompt.empty()
            .append(Component(string=CALLABLES_FOUND_SYSTEM_PROMPT_JSON))
            .append(GENERAL_STE_STYLE_INSTRUCTION)
            .append(USE_BACKTICKS_STYLE_INSTRUCTION)
            .into_str()
        )

    @classmethod
    def user_prompt(cls, symbol: RawSymbolData) -> str:
        user_prompt = (
            Prompt.empty()
            .append(NO_RESTATEMENT_STYLE_INSTRUCTION_FOR_SYMBOLS)
            .append(
                Component(
                    string=f"{CALLABLES_FOUND_USER_PROMPT}{symbol.name}\n\nFunction/Method Code:\n\n{symbol.symbol_code}"
                )
            )
        )
        if symbol.file_code:
            user_prompt.append(
                Component(string=f"\n\nFull File Code:\n\n{symbol.file_code}")
            )
        return user_prompt.into_str()

    @classmethod
    def child_to_ir(cls, symbol: RawSymbolData) -> type[IrData] | None:
        return None  # Go callables don't have children in our model

    @classmethod
    def child_to_field_name(cls, child: RawSymbolData) -> str:
        raise NotImplementedError("Callables should not have children")


class GoVariableData(VariableData):
    type: FieldNameWithRawContent
    description: FieldNameWithRawContent

    @classmethod
    def default_instance(cls, reified_symbol: ReifiedSymbol | None = None) -> Self:
        return cls(
            kind=FieldNameWithRawContent(field_name="Kind", content=""),
            description=FieldNameWithRawContent(field_name="Description", content=""),
        )

    @classmethod
    def system_prompt(cls, symbol: RawSymbolData) -> str:
        return (
            Prompt.empty()
            .append(Component(string=VARIABLES_FOUND_SYSTEM_PROMPT_JSON))
            .append(GENERAL_STE_STYLE_INSTRUCTION)
            .append(USE_BACKTICKS_STYLE_INSTRUCTION)
            .into_str()
        )

    @classmethod
    def user_prompt(cls, symbol: RawSymbolData) -> str:
        user_prompt = (
            Prompt.empty()
            .append(NO_RESTATEMENT_STYLE_INSTRUCTION_FOR_SYMBOLS)
            .append(
                Component(
                    string=f"{VARIABLES_FOUND_USER_PROMPT}\n\nVariable/Constant Code:\n\n{symbol.symbol_code}"
                )
            )
        )
        if symbol.file_code:
            user_prompt.append(
                Component(string=f"\n\nFull File Code:\n\n{symbol.file_code}")
            )
        return user_prompt.into_str()

    @classmethod
    def child_to_ir(cls, symbol: RawSymbolData) -> type[IrData] | None:
        return None

    @classmethod
    def child_to_field_name(cls, child: RawSymbolData) -> str:
        raise NotImplementedError("Variables should not have children")


class GoVariableGroupData(VariableData):
    description: FieldNameWithRawContent
    items: FourHeaderNamedContentNoNone

    @classmethod
    def default_instance(cls, reified_symbol: ReifiedSymbol | None = None) -> Self:
        return cls(
            items=FourHeaderNamedContentNoNone(content=[]),
            kind=FieldNameWithRawContent(field_name="Kind", content=""),
            description=FieldNameWithRawContent(field_name="Description", content=""),
        )

    @classmethod
    def system_prompt(cls, symbol: RawSymbolData) -> str:
        return (
            Prompt.empty()
            .append(Component(string=VARIABLE_GROUPS_FOUND_SYSTEM_PROMPT_JSON))
            .append(GENERAL_STE_STYLE_INSTRUCTION)
            .append(USE_BACKTICKS_STYLE_INSTRUCTION)
            .into_str()
        )

    @classmethod
    def user_prompt(cls, symbol: RawSymbolData) -> str:
        user_prompt = (
            Prompt.empty()
            .append(NO_RESTATEMENT_STYLE_INSTRUCTION_FOR_SYMBOLS)
            .append(
                Component(
                    string=f"{VARIABLE_GROUPS_FOUND_USER_PROMPT}\n\nVariable/Constant Code:\n\n{symbol.symbol_code}"
                )
            )
        )
        if symbol.file_code:
            user_prompt.append(
                Component(string=f"\n\nFull File Code:\n\n{symbol.file_code}")
            )
        return user_prompt.into_str()

    @classmethod
    def child_to_ir(cls, symbol: RawSymbolData) -> type[IrData] | None:
        return None

    @classmethod
    def child_to_field_name(cls, child: RawSymbolData) -> str:
        raise NotImplementedError("Variables should not have children")


class GoInterfaceData(IrData):
    description: FieldNameWithRawContent
    methods: ListedBacktickNameRawContentNoNone

    @classmethod
    def default_instance(cls, reified_symbol: ReifiedSymbol | None = None) -> Self:
        return cls(
            description=FieldNameWithRawContent(field_name="Description", content=""),
            methods=ListedBacktickNameRawContentNoNone(content=[]),
        )

    @classmethod
    def system_prompt(cls, symbol: RawSymbolData) -> str:
        return (
            Prompt.empty()
            .append(Component(string=INTERFACES_FOUND_SYSTEM_PROMPT_JSON))
            .append(GENERAL_STE_STYLE_INSTRUCTION)
            .append(USE_BACKTICKS_STYLE_INSTRUCTION)
            .into_str()
        )

    @classmethod
    def user_prompt(cls, symbol: RawSymbolData) -> str:
        user_prompt = (
            Prompt.empty()
            .append(NO_RESTATEMENT_STYLE_INSTRUCTION_FOR_SYMBOLS)
            .append(
                Component(
                    string=f"{INTERFACES_FOUND_USER_PROMPT}{symbol.name}\n\nInterface Code:\n\n{symbol.symbol_code}"
                )
            )
        )
        if symbol.file_code:
            user_prompt.append(
                Component(string=f"\n\nFull File Code:\n\n{symbol.file_code}")
            )
        return user_prompt.into_str()

    @classmethod
    def child_to_ir(cls, symbol: RawSymbolData) -> type[IrData] | None:
        return None

    @classmethod
    def child_to_field_name(cls, child: RawSymbolData) -> str:
        raise NotImplementedError("Interfaces should not have children")


# IrCollection Classes - simplified version


class GoDataStructureCollection(IrCollection):
    data: dict[str, GoDataStructureData | list[GoDataStructureData]]

    @classmethod
    def from_llm(cls, llm: ChatOpenAI, symbols_list: RawSymbolCollection) -> Self:
        return cls.from_llm_with_ir_data(GoDataStructureData, llm, symbols_list)


class GoCallableCollection(IrCollection):
    data: dict[str, GoCallableData | list[GoCallableData]]

    @classmethod
    def from_llm(cls, llm: ChatOpenAI, symbols_list: RawSymbolCollection) -> Self:
        return cls.from_llm_with_ir_data(GoCallableData, llm, symbols_list)


class GoVariableCollection(IrCollection):
    data: dict[str, GoVariableData | list[GoVariableData]]

    @classmethod
    def from_llm(cls, llm: ChatOpenAI, symbols_list: RawSymbolCollection) -> Self:
        return cls.from_llm_with_ir_data(GoVariableData, llm, symbols_list)


class GoVariableGroupCollection(IrCollection):
    data: dict[str, GoVariableGroupData | list[GoVariableGroupData]]

    @classmethod
    def from_llm(cls, llm: ChatOpenAI, symbols_list: RawSymbolCollection) -> Self:
        return cls.from_llm_with_ir_data(GoVariableGroupData, llm, symbols_list)


class GoInterfaceCollection(IrCollection):
    data: dict[str, GoInterfaceData | list[GoInterfaceData]]

    @classmethod
    def from_llm(cls, llm: ChatOpenAI, symbols_list: RawSymbolCollection) -> Self:
        return cls.from_llm_with_ir_data(GoInterfaceData, llm, symbols_list)


class GoDataStructureRawSymbolCollection(RawSymbolCollection):
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
                    delimiter=".",
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
                        == ds_symbol.raw.file_path  # NOTE: only include methods defined in the same file
                        and child.is_definition
                    ):
                        raw_symbol_data.children.append(
                            RawSymbolData.from_tree_sitter_raw_symbol(
                                ts_symbol=child.raw,
                                path=root_rel_path,
                                scope=ds_symbol.raw.name,
                                scope_relation=ScopeRelation.METHOD,
                                children=[],
                                reference_code=None,
                                delimiter=".",
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
                        delimiter=".",
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
                            delimiter=".",
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
        raise NotImplementedError("Tree-sitter should be used for Go data structures")

    def to_dict(self) -> dict[str, RawSymbolData]:
        return self.data


class GoInterfaceRawSymbolCollection(RawSymbolCollection):
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

        for interface_symbol in interface_symbols:
            if interface_symbol.raw.name is not None:
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
        output = (
            None
            if len(interface_raw_symbol_data) == 0
            else cls(data=interface_raw_symbol_data)
        )
        return output

    @classmethod
    def from_llm(cls, code: str, root_rel_path: str) -> Self:
        raise NotImplementedError("Tree-sitter should be used for Go interfaces")

    def to_dict(self) -> dict[str, RawSymbolData]:
        return self.data


class GoCallableRawSymbolCollection(RawSymbolCollection):
    data: dict[str, RawSymbolData]

    @classmethod
    def from_static_analysis(
        cls, code: str, root_rel_path: Path, reified_symbols: list[ReifiedSymbol]
    ) -> Self | None:
        callable_symbols = [
            sym
            for sym in reified_symbols
            if sym.raw.symbol_kind == SymbolKind.CALLABLE
            and sym.is_definition
            and sym.parent is None  # Only include top-level functions, not methods
        ]
        callable_raw_symbol_data = {}
        is_large_file = code_requires_multi_prompt(code)

        for callable_symbol in callable_symbols:
            if callable_symbol.raw.name is not None:
                raw_symbol_data = RawSymbolData.from_tree_sitter_raw_symbol(
                    ts_symbol=callable_symbol.raw,
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
                    reified_symbol=callable_symbol,
                )
                callable_raw_symbol_data[callable_symbol.raw.name] = raw_symbol_data
        output = (
            None
            if len(callable_raw_symbol_data) == 0
            else cls(data=callable_raw_symbol_data)
        )
        return output

    @classmethod
    def from_llm(cls, code: str, root_rel_path: str) -> Self:
        raise NotImplementedError("Tree-sitter should be used for Go callables")

    def to_dict(self) -> dict[str, RawSymbolData]:
        return self.data


class GoVariableRawSymbolCollection(RawSymbolCollection):
    data: dict[str, RawSymbolData | list[RawSymbolData]]

    @classmethod
    def from_static_analysis(
        cls, code: str, root_rel_path: Path, reified_symbols: list[ReifiedSymbol]
    ) -> Self | None:
        variable_symbols = [
            sym
            for sym in reified_symbols
            if sym.raw.symbol_kind == SymbolKind.VARIABLE
            and sym.raw.bespoke_data.kind in {"global_var", "global_const"}
        ]
        variable_raw_symbol_data = {}
        is_large_file = code_requires_multi_prompt(code)

        print(f"Found {len(variable_symbols)} variable symbols in {root_rel_path}")
        for variable_symbol in variable_symbols:
            if variable_symbol.raw.name is not None:
                raw_symbol_data = RawSymbolData.from_tree_sitter_raw_symbol(
                    ts_symbol=variable_symbol.raw,
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
                    reified_symbol=variable_symbol,
                )
                if variable_symbol.raw.name in variable_raw_symbol_data:
                    variable_raw_symbol_data[variable_symbol.raw.name].append(
                        raw_symbol_data
                    )
                else:
                    variable_raw_symbol_data[variable_symbol.raw.name] = [
                        raw_symbol_data
                    ]
        output = (
            None
            if len(variable_raw_symbol_data) == 0
            else cls(data=variable_raw_symbol_data)
        )
        return output

    @classmethod
    def from_llm(cls, code: str, root_rel_path: str) -> Self:
        raise NotImplementedError("Tree-sitter should be used for Go variables")

    def to_dict(self) -> dict[str, RawSymbolData]:
        return self.data


class GoVariableGroupRawSymbolCollection(RawSymbolCollection):
    data: dict[str, RawSymbolData | list[RawSymbolData]]

    @classmethod
    def from_static_analysis(
        cls, code: str, root_rel_path: Path, reified_symbols: list[ReifiedSymbol]
    ) -> Self | None:
        variable_symbols = [
            sym
            for sym in reified_symbols
            if sym.raw.symbol_kind == SymbolKind.VARIABLE
            and sym.raw.bespoke_data.kind in ["global_var_group", "global_const_group"]
        ]
        variable_raw_symbol_data = {}
        is_large_file = code_requires_multi_prompt(code)

        print(f"Found {len(variable_symbols)} variable symbols in {root_rel_path}")
        for variable_symbol in variable_symbols:
            if variable_symbol.raw.name is not None:
                raw_symbol_data = RawSymbolData.from_tree_sitter_raw_symbol(
                    ts_symbol=variable_symbol.raw,
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
                    reified_symbol=variable_symbol,
                )
                if variable_symbol.raw.bespoke_data.kind == "global_var_group":
                    raw_symbol_data.name = "Var Group"
                elif variable_symbol.raw.bespoke_data.kind == "global_const_group":
                    raw_symbol_data.name = "Const Group"
                if variable_symbol.raw.name in variable_raw_symbol_data:
                    variable_raw_symbol_data[variable_symbol.raw.name].append(
                        raw_symbol_data
                    )
                else:
                    variable_raw_symbol_data[variable_symbol.raw.name] = [
                        raw_symbol_data
                    ]
        output = (
            None
            if len(variable_raw_symbol_data) == 0
            else cls(data=variable_raw_symbol_data)
        )
        return output

    @classmethod
    def from_llm(cls, code: str, root_rel_path: str) -> Self:
        raise NotImplementedError("Tree-sitter should be used for Go variables")

    def to_dict(self) -> dict[str, RawSymbolData]:
        return self.data
