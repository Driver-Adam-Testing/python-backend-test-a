from pathlib import Path
from typing import Self

from pydantic import PrivateAttr
from utils.codemap_ctags import extract_symbols_w_ctags
from utils.models import ChatOpenAI

from .ir_common import (
    FieldNameWithBackTickContent,
    FieldNameWithRawContent,
    FnData,
    IrCollection,
    IrData,
    ListedBacktickNameRawContentNoNone,
    ListedRawContentNoNone,
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

RUST_DATA_STRUCTURE = {"enum", "struct"}
RUST_FUNCTIONS = {"function"}
RUST_METHODS = {"method"}
RUST_VARIABLES = {"constant", "variable"}
RUST_MACROS = {"macro"}
RUST_TRAITS = {"interface"}
RUST_IMPLEMENTATIONS = {"implementation"}


SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_RUST = """
You are an expert Rust programmer and a software engineering documentation expert. You write detailed documentation to explain code written in Rust.

You are skilled at explaining technical details as well as recognizing and articulating the key conceptual components and purpose of software.
"""

SOURCE_CODE_SMALL_SYSTEM_PROMPT_GENERAL_RUST = """
You are an expert Rust programmer and a software engineering documentation expert. You write detailed documentation to explain code written in Rust.

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
You will be given the content of a source code file. In a single paragraph of 3 to 5 sentences, explain the purpose of the file. Consider questions such as the following when providing your output:

- Does this code provide narrow or broad functionality?
- What kind of code is this? For example, is this code a short script, a collection of global variables or configuration variables, etc.?
"""

DATA_STRUCTURES_FOUND_SYSTEM_PROMPT_JSON = """
You are an expert Rust programmer and a software engineering documentation expert. You write detailed documentation to explain code written in Rust.

You focus on writing technical documentation for data structures in Rust. You are skilled at explaining technical details as well as recognizing and articulating the key conceptual components and purpose of software.

You will be given the name of a data structure to document and the source code where the data structure is defined.

When listing trait bounds in trait_bounds, only include trait bounds associated with the definition of the data structure. If a trait bound is associated with a method implementation but not the data structure itself, do not include it.

Your job is to describe the data structure. **Always respond using exactly the following JSON schema**:
{
    "type": <struct or enum>,
    "members": [
        {"name": <member_name1>, "content": <Terse 1 sentence description of the first struct field or enum variant>},
        {"name": <member_name2>, "content": <Terse 1 sentence description of the second struct field or enum variant>},
        ...
    ],
    "description": <one paragraph description of the data structure>,
    "trait_bounds": [<list of trait bounds for the data structure, if any>],
}

Return JSON according to the schema above. Do not use the format ```json ... ```, just return the JSON data.
"""

DATA_STRUCTURES_FOUND_USER_PROMPT = """
Summarize the data structure in the code provided below.

- When describing a data structure, provide detail that matches the complexity of the data structure. Large and complex data structures with many members should get longer explanations, while small ones a single sentence.

Data structure to document:
"""

METHODS_FOUND_SYSTEM_PROMPT_JSON = """
You are an expert Rust programmer and a software engineering documentation expert. You write detailed documentation to explain code written in Rust.

You focus on writing technical documentation for method implementations. You are skilled at explaining technical details as well as recognizing and articulating the key conceptual components and purpose of software.

You will be given the name of a method implementation to document and the source code where the method is implemented.

Identify the associated data structure in your description and always include any `self` argument (self, &self, or &mut self) that exists in a given method as an input.

Your job is to describe the method. **Always respond using exactly the following JSON schema**:
{
    "single_sentence": <terse single sentence description of the function>,
    "inputs": [
        {"name": <self, &self, or &mut self>, "content": <description of input argument 1>},
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

METHODS_FOUND_USER_PROMPT = """
Summarize the data structure method in the code provided below. Describe the inputs, control flow and logic, and output.

- When describing a data structure method, provide detail that matches the complexity of the method body. Large and complex methods should get longer explanations, while small ones much less.

Method to document:
"""

MACROS_FOUND_SYSTEM_PROMPT_JSON = """
You are an expert Rust programmer and a software engineering documentation expert. You write detailed documentation to explain code written in Rust.

You focus on writing technical documentation for macros in Rust. You are skilled at explaining technical details as well as recognizing and articulating the key conceptual components and purpose of software.

You will be given the name of a macro to document and the source code where the macro is defined.

Your job is to describe the macro. **Always respond using exactly the following JSON schema**:
{
    "type": <type of the macro, either declarative or procedural>,
    "description": <1 to 3 sentence description of the variable>,
    "logic": [
        <bullet point 1 describing logic implemented by the macro>,
        <Bullet point 2 describint logic implemenbed by the macro>,
        ...
    ],
    "use": <Terse 1 sentence description of how this macro is used>,
}

Return JSON according to the schema above. Do not use the format ```json ... ```, just return the JSON data.
"""

MACROS_FOUND_USER_PROMPT = """
Summarize the data structure in the code provided below.

- When describing a data structure, provide detail that matches the complexity of the data structure. Large and complex data structures with many members should get longer explanations, while small ones a single sentence.

Macro to document:
"""

FUNCTIONS_FOUND_SYSTEM_PROMPT_JSON = """
You are an expert Rust programmer and a software engineering documentation expert. You write detailed documentation to explain code written in Rust.

You focus on writing technical documentation for functions. You are skilled at explaining technical details as well as recognizing and articulating the key conceptual components and purpose of software.

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
Summarize the function in the code provided below. Describe the inputs, control flow and logic, and output.

- When describing a function, provide detail that matches the complexity of the function body. Large and complex functions should get longer explanations, while small ones much less.

Function to document:
"""

VARIABLES_FOUND_SYSTEM_PROMPT_JSON = """
You are an expert Rust programmer and a software engineering documentation expert. You write detailed documentation to explain code written in Python.

You focus on writing technical documentation for global variables and constants. You are skilled at explaining technical details as well as recognizing and articulating the key conceptual components and purpose of software.

You will be given the name of a global variable or constant to document and the source code where the data structure is defined.

Your job is to describe the global variable or constant. **Always respond using exactly the following JSON schema**:
{
    "type": <type of the variable>,
    "description": <1 to 3 sentence description of the variable>,
    "use": <Terse 1 sentence description of how this variable is used>,
}

Return JSON according to the schema above. Do not use the format ```json ... ```, just return the JSON data.
"""

VARIABLES_FOUND_USER_PROMPT = """
Summarize the global variable or constant in the code provided below.

- A global variable is declared at the top level scope. Local variables declared and used inside of functions are not global variables. You will be describing a global variable.
- When describing a variable, provide detail that matches the complexity of the variable. Large and complex global variables (e.g., containing large data structure instances) should get longer explanations, while small ones (e.g., one line definitions) much less.

Variable to document:
"""

TRAITS_FOUND_SYSTEM_PROMPT_JSON = """
You are an expert Rust programmer and a software engineering documentation expert. You write detailed documentation to explain code written in Rust.

You focus on writing technical documentation for data structures in Rust. You are skilled at explaining technical details as well as recognizing and articulating the key conceptual components and purpose of software.

You will be given the name of a Rust trait to document and the source code where the trait is defined.

When listing trait bounds in trait_bounds and generic types in generic_types, only include trait bounds and generic types associated with the definition of the trait (compared to any concrete implementations of the trait for specific data structures that may also be provided in the code).

Your job is to describe the data structure. **Always respond using exactly the following JSON schema**:
{
    "trait_bounds": [<list of concrete trait bounds for the trait, if any>],
    "generic_types": [<list of generic types for the trait, if any>],
    "methods": [
        {"name": <member_name1>, "content": <Terse 1 sentence description of the first method defined for the trait>},
        {"name": <member_name2>, "content": <Terse 1 sentence description of the second method defined for the trait>},
        ...
    ],
    "description": <one paragraph description of the trait>,
}

Return JSON according to the schema above. Do not use the format ```json ... ```, just return the JSON data.
"""

TRAITS_FOUND_USER_PROMPT = """
Summarize the trait in the code provided below.

- When describing a trait, provide detail that matches the complexity of the trait. Large and complex data structures with many methods, generics, and trait bounds should get longer explanations, while small ones a single sentence.

Trait to document:
"""


# IR Classes
class RustMacroData(IrData):
    type: FieldNameWithBackTickContent
    description: FieldNameWithRawContent
    logic: ListedRawContentNoNone
    use: FieldNameWithRawContent

    @classmethod
    def system_prompt(cls) -> str:
        return MACROS_FOUND_SYSTEM_PROMPT_JSON

    @classmethod
    def user_prompt(cls, symbol: RawSymbolData) -> str:
        user_prompt = f"{MACROS_FOUND_USER_PROMPT}{symbol.name}"
        if symbol.file_code:
            user_prompt += f"\n\nCode:\n\n{symbol.file_code}"
        else:
            user_prompt += f"\n\nCode:\n\n{symbol.symbol_code}"
        return user_prompt

    @classmethod
    def child_to_ir(cls, symbol: RawSymbolData) -> type[IrData] | None:
        raise NotImplementedError("Macros should not have children")

    @classmethod
    def child_to_field_name(cls, child: RawSymbolData) -> str:
        raise NotImplementedError("Macros should not have children")

    @classmethod
    def default_instance(cls) -> Self:
        return cls(
            type="",
            description="",
            logic=[],
            use="",
        )


class RustMacroCollection(IrCollection):
    data: dict[str, RustMacroData | list[RustMacroData]]

    @classmethod
    def from_llm(cls, llm: ChatOpenAI, symbols_list: RawSymbolCollection) -> Self:
        return cls.from_llm_with_ir_data(RustMacroData, llm, symbols_list)


class RustTraitData(IrData):
    trait_bounds: ListedRawContentNoNone
    generic_types: ListedRawContentNoNone
    methods: ListedBacktickNameRawContentNoNone
    description: FieldNameWithRawContent

    @classmethod
    def system_prompt(cls) -> str:
        return TRAITS_FOUND_SYSTEM_PROMPT_JSON

    @classmethod
    def user_prompt(cls, symbol: RawSymbolData) -> str:
        user_prompt = f"{TRAITS_FOUND_USER_PROMPT}{symbol.name}"
        if symbol.file_code:
            user_prompt += f"\n\nCode:\n\n{symbol.file_code}"
        else:
            user_prompt += f"\n\nCode:\n\n{symbol.symbol_code}"
        return user_prompt

    @classmethod
    def child_to_ir(cls, symbol: RawSymbolData) -> type[IrData] | None:
        raise NotImplementedError("Traits should not have children")

    @classmethod
    def child_to_field_name(cls, child: RawSymbolData) -> str:
        raise NotImplementedError("Traits should not have children")

    @classmethod
    def default_instance(cls) -> Self:
        return cls(
            trait_bounds=[],
            generic_types=[],
            methods=[],
            description="",
        )


class RustTraitCollection(IrCollection):
    data: dict[str, RustTraitData | list[RustTraitData]]

    @classmethod
    def from_llm(cls, llm: ChatOpenAI, symbols_list: RawSymbolCollection) -> Self:
        return cls.from_llm_with_ir_data(RustTraitData, llm, symbols_list)


class RustDataStructureData(IrData):
    type: FieldNameWithBackTickContent
    members: ListedBacktickNameRawContentNoNone
    description: FieldNameWithRawContent
    trait_bounds: ListedRawContentNoNone
    _supported_child_ordering: list[str] = PrivateAttr(
        default=[ScopeRelation.METHOD, ScopeRelation.NESTED_DATA_STRUCTURE]
    )

    @classmethod
    def system_prompt(cls) -> str:
        return DATA_STRUCTURES_FOUND_SYSTEM_PROMPT_JSON

    @classmethod
    def user_prompt(cls, symbol: RawSymbolData) -> str:
        user_prompt = f"{DATA_STRUCTURES_FOUND_USER_PROMPT}{symbol.name}"
        if symbol.file_code:
            user_prompt += f"\n\nCode:\n\n{symbol.file_code}"
        else:
            user_prompt += f"\n\nCode:\n\n{symbol.symbol_code}"
        return user_prompt

    @classmethod
    def child_to_ir(cls, symbol: RawSymbolData) -> type[IrData] | None:
        mapping = {
            SymbolKind.CALLABLE: RustMethodData,
            SymbolKind.DATA_STRUCTURE: None,
        }
        return mapping.get(symbol.symbol_kind)

    @classmethod
    def child_to_field_name(cls, child: RawSymbolData) -> str:
        mapping = {
            SymbolKind.CALLABLE: ScopeRelation.METHOD,
            SymbolKind.DATA_STRUCTURE: ScopeRelation.NESTED_DATA_STRUCTURE,
        }
        return mapping.get(child.symbol_kind)

    @classmethod
    def default_instance(cls) -> Self:
        return cls(
            type="",
            members=[],
            description="Implemented elsewhere",
            trait_bounds=[],
        )


class RustDataStructureCollection(IrCollection):
    data: dict[str, RustDataStructureData | list[RustDataStructureData]]

    @classmethod
    def from_llm(cls, llm: ChatOpenAI, symbols_list: RawSymbolCollection) -> Self:
        return cls.from_llm_with_ir_data(RustDataStructureData, llm, symbols_list)


class RustMethodData(FnData):
    @classmethod
    def system_prompt(cls) -> str:
        return METHODS_FOUND_SYSTEM_PROMPT_JSON

    @classmethod
    def user_prompt(cls, symbol: RawSymbolData) -> str:
        # TODO: for overloaded case
        user_prompt = f"{METHODS_FOUND_USER_PROMPT}{symbol.name}"
        if symbol.file_code:
            user_prompt += f"\n\nCode:\n\n{symbol.file_code}"
        else:
            user_prompt += f"\n\nCode:\n\n{symbol.symbol_code}"
        return user_prompt

    @classmethod
    def child_to_ir(cls, symbol: RawSymbolData) -> IrData | None:
        raise NotImplementedError("Methods should not have children")

    @classmethod
    def child_to_field_name(cls, child: RawSymbolData) -> str:
        raise NotImplementedError("Methods should not have children")


class RustFnData(FnData):
    @classmethod
    def system_prompt(cls) -> str:
        return FUNCTIONS_FOUND_SYSTEM_PROMPT_JSON

    @classmethod
    def user_prompt(cls, symbol: RawSymbolData) -> str:
        user_prompt = f"{FUNCTIONS_FOUND_USER_PROMPT}{symbol.name}"
        if symbol.file_code:
            user_prompt += f"\n\nCode:\n\n{symbol.file_code}"
        else:
            user_prompt += f"\n\nCode:\n\n{symbol.symbol_code}"
        return user_prompt

    @classmethod
    def child_to_ir(cls, symbol: RawSymbolData) -> IrData | None:
        raise NotImplementedError("Functions should not have children")

    @classmethod
    def child_to_field_name(cls, child: RawSymbolData) -> str:
        raise NotImplementedError("Functions should not have children")


class RustFnCollection(IrCollection):
    data: dict[str, RustFnData | list[RustFnData]]

    @classmethod
    def from_llm(cls, llm: ChatOpenAI, symbols_list: RawSymbolCollection) -> Self:
        return cls.from_llm_with_ir_data(RustFnData, llm, symbols_list)


class RustVariableData(VariableData):
    @classmethod
    def system_prompt(cls) -> str:
        return VARIABLES_FOUND_SYSTEM_PROMPT_JSON

    @classmethod
    def user_prompt(cls, symbol: RawSymbolData) -> str:
        user_prompt = f"{VARIABLES_FOUND_USER_PROMPT}{symbol.name}"
        if symbol.file_code:
            user_prompt += f"\n\nCode:\n\n{symbol.file_code}"
        else:
            user_prompt += f"\n\nCode:\n\n{symbol.symbol_code}"
        return user_prompt

    @classmethod
    def child_to_ir(cls, symbol: RawSymbolData) -> IrData | None:
        raise NotImplementedError("Variables should not have children")

    @classmethod
    def child_to_field_name(cls, child: RawSymbolData) -> str:
        raise NotImplementedError("Variables should not have children")


class RustVariableCollection(IrCollection):
    data: dict[str, RustVariableData | list[RustVariableData]]

    @classmethod
    def from_llm(cls, llm: ChatOpenAI, symbols_list: RawSymbolCollection) -> Self:
        return cls.from_llm_with_ir_data(RustVariableData, llm, symbols_list)


class RustDataStructureRawSymbolCollection(RawSymbolCollection):
    data: dict[str, RawSymbolData | list[RawSymbolData]]

    @classmethod
    def from_static_analysis(cls, code: str, root_rel_path: Path) -> Self:
        is_multi_prompt = code_requires_multi_prompt(code)

        symbols = extract_symbols_w_ctags(
            root_rel_path=root_rel_path, file_content=code
        )

        global_method_counts = {}
        data_struct_raw_symbol_data = {}
        for s in symbols:
            if s["kind"] in RUST_METHODS and not s["name"].startswith("__anon"):
                global_method_counts[s["name"]] = (
                    global_method_counts.get(s["name"], 0) + 1
                )
            if s["kind"] in RUST_DATA_STRUCTURE and not s["name"].startswith("__anon"):
                data_struct_raw_symbol_data[s["name"]] = create_raw_symbol_via_ctags(
                    ctags_symbol=s,
                    root_rel_path=root_rel_path,
                    code=code,
                    symbol_kind=SymbolKind.DATA_STRUCTURE,
                    scope_relation=None,
                    delimiter="::",
                    is_multi_prompt=is_multi_prompt,
                )

        for s in symbols:
            if (
                s.get("scope")
                and not s["name"].startswith("__anon")
                and (s.get("kind") in RUST_METHODS)
                and (s.get("scopeKind") in RUST_IMPLEMENTATIONS)
            ):
                if s["scope"] not in data_struct_raw_symbol_data:
                    data_struct_raw_symbol_data[s["scope"]] = RawSymbolData(
                        parser_kind=ParserKind.UCTAGS,
                        symbol_kind=SymbolKind.DATA_STRUCTURE,
                        name=s["scope"],
                        path=root_rel_path,
                        scope=None,
                        scope_relation=None,
                        children=[],
                        start_line=None,
                        end_line=None,
                        symbol_code=None,
                        file_code=None,
                        reference_code=None,
                        delimiter="::",
                    )

                is_overloaded = global_method_counts[s["name"]] > 1
                data_struct_raw_symbol_data[s["scope"]].children.append(
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
                s.get("scope")
                and not s["name"].startswith("__anon")
                and (s.get("kind") in RUST_DATA_STRUCTURE)
                and (s.get("scopeKind") in RUST_DATA_STRUCTURE)
            ):
                if s["scope"] in data_struct_raw_symbol_data:
                    data_struct_raw_symbol_data[s["scope"]].children.append(
                        create_raw_symbol_via_ctags(
                            ctags_symbol=s,
                            root_rel_path=root_rel_path,
                            code=code,
                            symbol_kind=SymbolKind.DATA_STRUCTURE,
                            scope_relation=ScopeRelation.NESTED_DATA_STRUCTURE,
                            delimiter="::",
                            is_multi_prompt=is_multi_prompt,
                        )
                    )
        output = (
            None
            if len(data_struct_raw_symbol_data) == 0
            else cls(data=data_struct_raw_symbol_data)
        )
        return output

    @classmethod
    def from_llm(cls, code: str, root_rel_path: str) -> Self:
        raise NotImplementedError("Static analysis should be used for Rust classes")

    def to_dict(self) -> dict[str, RawSymbolData]:
        return self.data


class RustFnRawSymbolCollection(RawSymbolCollection):
    data: dict[str, RawSymbolData | list[RawSymbolData]]

    @classmethod
    def from_static_analysis(cls, code: str, root_rel_path: Path) -> Self:
        is_multi_prompt = code_requires_multi_prompt(code)

        symbols = extract_symbols_w_ctags(
            root_rel_path=root_rel_path, file_content=code
        )

        fn_raw_symbol_data = {}
        for s in symbols:
            if s["kind"] in RUST_FUNCTIONS and not s["name"].startswith("__anon"):
                fn_raw_symbol_data[s["name"]] = create_raw_symbol_via_ctags(
                    ctags_symbol=s,
                    root_rel_path=root_rel_path,
                    code=code,
                    symbol_kind=SymbolKind.CALLABLE,
                    scope_relation=None,
                    delimiter="::",
                    is_multi_prompt=is_multi_prompt,
                )

        output = None if len(fn_raw_symbol_data) == 0 else cls(data=fn_raw_symbol_data)
        return output

    @classmethod
    def from_llm(cls, code: str, root_rel_path: str) -> Self:
        raise NotImplementedError("Static analysis should be used for Rust functions")

    def to_dict(self) -> dict[str, RawSymbolData]:
        return self.data


class RustVariablesRawSymbolCollection(RawSymbolCollection):
    data: dict[str, RawSymbolData | list[RawSymbolData]]

    @classmethod
    def from_static_analysis(cls, code: str, root_rel_path: Path) -> Self:
        is_multi_prompt = code_requires_multi_prompt(code)

        symbols = extract_symbols_w_ctags(
            root_rel_path=root_rel_path, file_content=code
        )

        variable_raw_symbol_data = {}
        for s in symbols:
            if s["kind"] in RUST_VARIABLES and not s.get("scopeKind"):
                variable_raw_symbol_data[s["name"]] = create_raw_symbol_via_ctags(
                    ctags_symbol=s,
                    root_rel_path=root_rel_path,
                    code=code,
                    symbol_kind=SymbolKind.VARIABLE,
                    scope_relation=None,
                    delimiter="::",
                    is_multi_prompt=is_multi_prompt,
                )

        output = (
            None
            if len(variable_raw_symbol_data) == 0
            else cls(data=variable_raw_symbol_data)
        )
        return output

    @classmethod
    def from_llm(cls, code: str, root_rel_path: str) -> Self:
        raise NotImplementedError("Static analysis should be used for Rust functions")

    def to_dict(self) -> dict[str, RawSymbolData]:
        return self.data


class RustMacroRawSymbolCollection(RawSymbolCollection):
    data: dict[str, RawSymbolData | list[RawSymbolData]]

    @classmethod
    def from_static_analysis(cls, code: str, root_rel_path: Path) -> Self:
        return default_ctags_analysis(
            collection_cls=cls,
            code=code,
            root_rel_path=root_rel_path,
            symbol_kind=SymbolKind.CALLABLE,
            ctags_kinds=RUST_MACROS,
            delimiter="::",
            add_symbol_padding=False,
        )

    @classmethod
    def from_llm(cls, code: str, root_rel_path: str) -> Self:
        raise NotImplementedError("Static analysis should be used for Rust functions")

    def to_dict(self) -> dict[str, RawSymbolData]:
        return self.data


class RustTraitsRawSymbolCollection(RawSymbolCollection):
    data: dict[str, RawSymbolData | list[RawSymbolData]]

    @classmethod
    def from_static_analysis(cls, code: str, root_rel_path: Path) -> Self:
        return default_ctags_analysis(
            collection_cls=cls,
            code=code,
            root_rel_path=root_rel_path,
            symbol_kind=SymbolKind.DATA_STRUCTURE,
            ctags_kinds=RUST_TRAITS,
            delimiter="::",
            add_symbol_padding=False,
        )

    @classmethod
    def from_llm(cls, code: str, root_rel_path: str) -> Self:
        raise NotImplementedError("Static analysis should be used for Rust functions")

    def to_dict(self) -> dict[str, RawSymbolData]:
        return self.data
