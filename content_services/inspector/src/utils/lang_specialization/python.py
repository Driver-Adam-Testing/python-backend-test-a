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
from utils.treesitter_drivers.python_driver import PyDriverTree

from .ir_common import (
    FieldNameWithBackTickContent,
    FieldNameWithBulletedContent,
    FieldNameWithRawContent,
    IrCollection,
    IrData,
    ListedBacktickNameRawContentNoNone,
    ListedBacktickNameRawContentWithNone,
    ListedCommaCombinedBackTickRawContentNoNone,
    ListedRawContentNoNone,
    ListedRawContentWithNone,
    RawContent,
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

PY_CLASS = {"class"}
PY_FUNCTIONS = {"function"}
PY_METHODS = {"member"}
PY_VARIABLES = {"variable"}


SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_PY = """
You are an expert Python programmer and a software engineering documentation expert. You write detailed documentation to explain code written in Python.

You are skilled at explaining technical details as well as recognizing and articulating the key conceptual components and purpose of software.
"""

SOURCE_CODE_SMALL_SYSTEM_PROMPT_GENERAL_PY = """
You are an expert Python programmer and a software engineering documentation expert. You write detailed documentation to explain code written in Python.

You are skilled at explaining technical details as well as recognizing and articulating the key conceptual components and purpose of software.

You specialize in effectively describing small and short source code files. Your goal is to be terse and clear, since the source code you are describing is small and simple.
"""

SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT = """
You will be given the content of a source code file. In 1 or 2 paragraphs, explain the purpose of the file.

When writing your paragraphs, do not use speculative language.

When writing your paragraphs, consider questions like the following. You do not need to explicitly state these ideas, they are just given as examples of the kind of information to provide:

- Does this code provide narrow or broad functionality?
- What are the most important technical components?
- Is this code a collection of many different components? If so, what is the common theme or purpose?
- What kind of code is this? For example, is this code clearly as script, a library file intended to be imported elsewhere, etc.?
- Does it define public APIs or external interfaces?
"""

SOURCE_CODE_SMALL_PURPOSE_USER_PROMPT = """
You will be given the content of a source code file. In a single paragraph of 3 to 5 sentences, explain the purpose of the file.

Consider questions such as the following when providing your output:

- Does this code provide narrow or broad functionality?
- What kind of code is this? For example, is this code a short script, a collection of global variables or configuration variables, etc.?
"""

TECHNICAL_CONCEPTS = """
You will be given the content of a source code file. In a single paragraph of 3 to 5 sentences, describe the important technical features and their interactions in the file.

In writing your description, write about about the conceptual use cases, applications, logic, and component interactions instead of focusing on particular classes, functions, variables, etc.
"""

CLASSES_FOUND_SYSTEM_PROMPT_JSON = """
You are an expert Python programmer and a software engineering documentation expert. You write detailed documentation to explain code written in Python.

You focus on writing technical documentation for classes in Python. You are skilled at explaining technical details as well as recognizing and articulating the key conceptual components and purpose of software.

You will be given the name of a class to document and the source code where the class is defined.

IMPORTANT: members should ONLY include instance and class variables or properties of the class. Do **not** include methods in the members list of the data structure.

For the list of decorators, provide the decorator name prepended with @ for each identified decorator (e.g.: `@dataclass`). Only provide the name of each decorator and **DO NOT** list or inlcude arguments to decorators (e.g., provide `@dataclass` in your lost and not `@dataclass(frozen=True)` in your list of decorators). **ONLY** include decorators applied to the class itself, if any, not decorators applied to instance variables, class variables, methods, etc. of the class.

Your job is to describe the class. **Always respond using exactly the following JSON schema**:
{
    "decorators": [<`@decorator1_name`>, <`@decorator2_name`>, ...],
    "members": [
        {"name": <member_name1>, "content": <Terse 1 sentence description of the first instance or class variable>},
        {"name": <member_name2>, "content": <Terse 1 sentence description of the second instance or class variable>},
        ...
    ],
    "description": <one paragraph description of the class>,
}

Return JSON according to the schema above. Do not use the format ```json ... ```, just return the JSON data.
"""

CLASSES_FOUND_USER_PROMPT = """
Summarize the class in the code provided below.

- When describing a class, provide detail that matches the complexity of the class. Large and complex classes with many members should get longer explanations, while small ones a single sentence.

Class to document:
"""

METHODS_FOUND_SYSTEM_PROMPT_JSON = """
You are an expert Python programmer and a software engineering documentation expert. You write detailed documentation to explain code written in Python.

You focus on writing technical documentation for class methods. You are skilled at explaining technical details as well as recognizing and articulating the key conceptual components and purpose of software.

You will be given the name of a class method to document and the source code where the function is defined.

Identify the associated class in your description and always include any `self` or `cls` arguments that exist in a given method as an input.

Your job is to describe the function. **Always respond using exactly the following JSON schema**:
{
    "single_sentence": <terse single sentence description of the function>,
    "inputs": [
        {"name": <input_arg1>, "content": <description of input argument 1>},
        {"name": <input_arg2>, "content": <description of input argument 2>},
        ...
    ],
    "logic_and_control_flow": [
        <bullet point 1 for description of control flow>,
        <bullet point 2 for description of control flow>,
        ...
    ],
    "output": <description of output>
}

Return JSON according to the schema above. Do not use the format ```json ... ```, just return the JSON data.
"""

METHODS_FOUND_USER_PROMPT = """
Summarize the class method in the code provided below. Describe the inputs, control flow and logic, and output.

- When describing a class method, provide detail that matches the complexity of the function body. Large and complex functions should get longer explanations, while small ones much less.

Method to document:
"""

DATA_STRUCTURES_FOUND_SYSTEM_PROMPT_JSON = """
You are an expert Python programmer and a software engineering documentation expert. You write detailed documentation to explain code written in Python.

You focus on writing technical documentation for data structures, typically classes in Python. You are skilled at explaining technical details as well as recognizing and articulating the key conceptual components and purpose of software.

You will be given the name of a data structure to document and the source code where the data structure is defined.

Your job is to describe the data structure. **Always respond using exactly the following JSON schema**:
{
    "type": <type of the data structure>,
    "members": [
        {"name": <member_name1>, "content": <Terse 1 sentence description of the first member, field, or attribute>},
        {"name": <member_name2>, "content": <Terse 1 sentence description of the second member, field, or attribute>},
        ...
    ],
    "description": <one paragraph description of the data structure>,
}

Return JSON according to the schema above. Do not use the format ```json ... ```, just return the JSON data.
"""

DATA_STRUCTURES_FOUND_USER_PROMPT = """
Summarize the data structure in the code provided below.

- A data structure is custom or compound type in a given programming language, such as structs, classes, or enums. Functions, methods, and variables are not data structures. In Python, custom data structures are typically defined as classes.
- When describing an important data structure, provide detail that matches the complexity of the data structure. Large and complex data structures should get longer explanations, while small ones a single sentence.

Data structure to document:
"""


FUNCTIONS_OR_METHODS_FOUND_SYSTEM_PROMPT_JSON = """
You are an expert Python programmer and a software engineering documentation expert. You write detailed documentation to explain code written in Python.

You focus on writing technical documentation for functions and methods. You are skilled at explaining technical details as well as recognizing and articulating the key conceptual components and purpose of software.

You will be given the name of a function or a method to document and the source code where the function or method is defined.

For the list of decorators applied to this function or method, provide the decorator name prepended with @ for each identified decorator (e.g.: `@classmethod`). Only provide the name of each decorator and **DO NOT** list or include any arguments provided to the decorator (e.g., write `@log` not `@log(level="DEBUG")` in your list of decorators).

Your job is to describe the function or method. **Always respond using exactly the following JSON schema**:
{
    "single_sentence": <terse single sentence description of the function or method>,
    "decorators": [<`@decorator1_name`>, <`@decorator2_name`>, ...],
    "inputs": [
        {"name": <input_arg1>, "content": <description of input argument 1>},
        {"name": <input_arg2>, "content": <description of input argument 2>},
        ...
    ],
    "logic_and_control_flow": [
        <bullet point 1 for description of control flow>,
        <bullet point 2 for description of control flow>,
        ...
    ],
    "output": <description of output>
}

Return JSON according to the schema above. Do not use the format ```json ... ```, just return the JSON data.
"""

FUNCTIONS_OR_METHODS_FOUND_USER_PROMPT = """
Summarize the function or method in the code provided below. Describe the inputs, control flow and logic, and output.

- When describing a function or method, provide detail that matches the complexity of the function or method body. Large and complex functions or methods should get longer explanations, while small ones much less.

Function or method to document:
"""


VARIABLES_FOUND_SYSTEM_PROMPT_JSON = """
You are an expert Python programmer and a software engineering documentation expert. You write detailed documentation to explain code written in Python.

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
- When describing a variable, provide detail that matches the complexity of the variable. Large and complex global variables (e.g., containing large class instances) should get longer explanations, while small ones (e.g., one line definitions) much less.

Variable to document:
"""


# IR data classes
class PyVariableData(VariableData):
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
            .append(Component(string=f"{VARIABLES_FOUND_USER_PROMPT}\n{symbol.name}"))
            .append(NO_RESTATEMENT_STYLE_INSTRUCTION_FOR_SYMBOLS)
            .append(Component(string=f"Variable Code:\n\n{symbol.symbol_code}"))
        )
        if symbol.file_code:
            user_prompt.append(
                Component(string=f"\n\nFull File Code:\n\n{symbol.file_code}")
            )
        return user_prompt.into_str()

    @classmethod
    def child_to_ir(cls, symbol: RawSymbolData) -> type[IrData] | None:
        raise NotImplementedError("Variables should not have children")

    @classmethod
    def child_to_field_name(cls, child: RawSymbolData) -> str:
        raise NotImplementedError("Variables should not have children")


class PyVariableCollection(IrCollection):
    data: dict[str, PyVariableData | list[PyVariableData]]

    @classmethod
    def from_llm(cls, llm: ChatOpenAI, symbols_list: RawSymbolCollection) -> Self:
        return cls.from_llm_with_ir_data(PyVariableData, llm, symbols_list)


class PyFnData(IrData):
    single_sentence: RawContent
    decorators: ListedCommaCombinedBackTickRawContentNoNone
    inputs: ListedBacktickNameRawContentWithNone
    logic_and_control_flow: ListedRawContentWithNone
    output: FieldNameWithRawContent

    @classmethod
    def default_instance(cls, reified_symbol: ReifiedSymbol | None = None) -> Self:
        return cls(
            single_sentence=RawContent(content=""),
            inputs=ListedBacktickNameRawContentWithNone(content=[]),
            logic_and_control_flow=ListedBacktickNameRawContentWithNone(content=[]),
            output=FieldNameWithBulletedContent(content=""),
        )

    @classmethod
    def system_prompt(cls, symbol: RawSymbolData) -> str:
        return (
            Prompt.empty()
            .append(Component(string=FUNCTIONS_OR_METHODS_FOUND_SYSTEM_PROMPT_JSON))
            .append(GENERAL_STE_STYLE_INSTRUCTION)
            .append(USE_BACKTICKS_STYLE_INSTRUCTION)
            .into_str()
        )

    @classmethod
    def user_prompt(cls, symbol: RawSymbolData) -> str:
        user_prompt = Prompt.empty().append(
            NO_RESTATEMENT_STYLE_INSTRUCTION_FOR_SYMBOLS
        )
        if (
            symbol.reified_symbol is not None
            and symbol.reified_symbol.parent is not None
            and symbol.reified_symbol.parent.raw.symbol_code is not None
        ):
            user_prompt.append(
                Component(
                    string=f"{FUNCTIONS_OR_METHODS_FOUND_USER_PROMPT}{symbol.name}\n\nMethod Code:\n\n{symbol.symbol_code}"
                )
            ).append(
                Component(
                    string=f"\n\nParent class code:\n\n{symbol.reified_symbol.parent.raw.symbol_code}"
                )
            )
        else:
            user_prompt.append(
                Component(
                    string=f"{FUNCTIONS_OR_METHODS_FOUND_USER_PROMPT}{symbol.name}\n\nFunction Code:\n\n{symbol.symbol_code}"
                )
            )

        if symbol.file_code:
            user_prompt.append(
                Component(string=f"\n\nFull File Code:\n\n{symbol.file_code}")
            )
        return user_prompt.into_str()

    @classmethod
    def child_to_ir(cls, symbol: RawSymbolData) -> type[IrData] | None:
        raise NotImplementedError("Functions should not have children")

    @classmethod
    def child_to_field_name(cls, child: RawSymbolData) -> str:
        raise NotImplementedError("Functions should not have children")


class PyFnCollection(IrCollection):
    data: dict[str, PyFnData | list[PyFnData]]

    @classmethod
    def from_llm(cls, llm: ChatOpenAI, symbols_list: RawSymbolCollection) -> Self:
        return cls.from_llm_with_ir_data(PyFnData, llm, symbols_list)


class PyClassData(IrData):
    decorators: ListedCommaCombinedBackTickRawContentNoNone
    members: ListedBacktickNameRawContentNoNone
    description: FieldNameWithRawContent
    _supported_child_ordering: list[str] = PrivateAttr(
        default=[ScopeRelation.METHOD, ScopeRelation.NESTED_CLASS]
    )

    @classmethod
    def default_instance(cls, reified_symbol: ReifiedSymbol | None = None) -> Self:
        return cls(
            description=FieldNameWithRawContent(content="Implemented elsewhere"),
            type=FieldNameWithBackTickContent(content="N/A"),
            members=ListedBacktickNameRawContentNoNone(content=[]),
            inherits_from=ListedRawContentNoNone(content=[]),
        )

    @classmethod
    def system_prompt(cls, symbol: RawSymbolData) -> str:
        return (
            Prompt.empty()
            .append(Component(string=CLASSES_FOUND_SYSTEM_PROMPT_JSON))
            .append(GENERAL_STE_STYLE_INSTRUCTION)
            .append(USE_BACKTICKS_STYLE_INSTRUCTION)
            .into_str()
        )

    @classmethod
    def user_prompt(cls, symbol: RawSymbolData) -> str:
        user_prompt = Prompt.empty().append(
            NO_RESTATEMENT_STYLE_INSTRUCTION_FOR_SYMBOLS
        )
        user_prompt.append(
            Component(
                string=f"{CLASSES_FOUND_USER_PROMPT}{symbol.name}\n\nClass Code:\n\n{symbol.symbol_code}"
            )
        )
        if symbol.file_code:
            user_prompt.append(
                Component(string=f"\n\nFull File Code:\n\n{symbol.file_code}")
            )
        return user_prompt.into_str()

    @classmethod
    def child_to_ir(cls, symbol: RawSymbolData) -> type[IrData] | None:
        mapping = {
            SymbolKind.CALLABLE: PyFnData,
            SymbolKind.CLASS: None,  # for child classes and structs we just list them
        }
        return mapping.get(symbol.symbol_kind)

    @classmethod
    def child_to_field_name(cls, child: RawSymbolData) -> str:
        mapping = {
            SymbolKind.CALLABLE: ScopeRelation.METHOD,
            SymbolKind.CLASS: ScopeRelation.NESTED_CLASS,
        }
        return mapping.get(child.symbol_kind)


class PyClassCollection(IrCollection):
    data: dict[str, PyClassData | list[PyClassData]]

    @classmethod
    def from_llm(cls, llm: ChatOpenAI, symbols_list: RawSymbolCollection) -> Self:
        return cls.from_llm_with_ir_data(PyClassData, llm, symbols_list)


# Symbol extraction classes
class PyVariableRawSymbolCollection(RawSymbolCollection):
    data: dict[str, RawSymbolData]

    @classmethod
    def from_static_analysis(cls, code: str, root_rel_path: Path) -> Self | None:
        driver_tree = PyDriverTree.from_code(code, root_rel_path)
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
        raise NotImplementedError("Static analysis should be used for Py variables")

    def to_dict(self) -> dict[str, RawSymbolData]:
        return self.data


class PyFnRawSymbolCollection(RawSymbolCollection):
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
            if ts_symbol.name is not None and symbol_parent_kind != SymbolKind.CLASS:
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
        raise NotImplementedError("Static analysis should be used for Py functions")

    def to_dict(self) -> dict[str, RawSymbolData]:
        return self.data


class PyClassRawSymbolCollection(RawSymbolCollection):
    data: dict[str, RawSymbolData]

    @classmethod
    def from_static_analysis(
        cls, code: str, root_rel_path: Path, reified_symbols: list[ReifiedSymbol]
    ) -> Self | None:
        ds_symbols = [
            sym
            for sym in reified_symbols
            if sym.raw.symbol_kind == SymbolKind.CLASS and sym.is_definition
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
            if callable_symbol.parent.raw.symbol_kind == SymbolKind.CLASS:
                parent_name = callable_symbol.parent.raw.name
                if parent_name not in data_structure_raw_symbol_data:
                    data_structure_raw_symbol_data[parent_name] = RawSymbolData(
                        parser_kind=ParserKind.TREE_SITTER,
                        symbol_kind=SymbolKind.CLASS,
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
        raise NotImplementedError("Static analysis should be used for Py classes")

    def to_dict(self) -> dict[str, RawSymbolData]:
        return self.data


class PyImportRawSymbolCollection(RawSymbolCollection):
    data: dict[str, RawSymbolData]

    @classmethod
    def from_static_analysis(cls, code: str, root_rel_path: Path) -> Self | None:
        driver_tree = PyDriverTree.from_code(code, root_rel_path)
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
        raise NotImplementedError("Static analysis should be used for Python imports")

    def to_dict(self) -> dict[str, RawSymbolData]:
        return self.data
