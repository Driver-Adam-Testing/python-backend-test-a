from pathlib import Path
from typing import Self

from shared.agent.chat_openai import ChatOpenAI
from shared.inspector.utils.treesitter_drivers.c_cpp_driver import CppCDriverTree
from shared.prompts.structured_prompting import (
    GENERAL_STE_STYLE_INSTRUCTION,
    NO_RESTATEMENT_STYLE_INSTRUCTION_FOR_SYMBOLS,
    USE_BACKTICKS_STYLE_INSTRUCTION,
    Component,
    Prompt,
)

from .ir_common import (
    DataStructureData,
    FnData,
    FnDeclData,
    IrCollection,
    IrData,
    VariableData,
)
from .symbol_common import (
    RawSymbolCollection,
    RawSymbolData,
    ReifiedSymbol,
    SymbolKind,
    code_requires_multi_prompt,
)

C_VARIABLES = {"variable", "externvar"}


SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_C = """
You are an expert C programmer and a software engineering documentation expert. You write detailed documentation to explain code written in C.

You are skilled at explaining technical details as well as recognizing and articulating the key conceptual components and purpose of software.
"""

SOURCE_CODE_SMALL_SYSTEM_PROMPT_GENERAL_C = """
You are an expert C programmer and a software engineering documentation expert. You write detailed documentation to explain code written in C.

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
- What kind of code is this? For example, is this code clearly an executable (e.g., main.c), a C header file, a C file or library intended to be imported elsewhere?
- Does it define public APIs or external interfaces?
"""

SOURCE_CODE_SMALL_PURPOSE_USER_PROMPT = """
You will be given the content of a source code file. In a single paragraph of 3 to 5 sentences, explain the purpose of the file. Consider questions such as the following when providing your output:

- What kind of code is this? For example, is this code a short script, a simple C header file, a collection of global variables or configuration variables, etc.?
"""

TECHNICAL_CONCEPTS = """
You will be given the content of a source code file. In a single paragraph of 3 to 5 sentences, describe the important technical features and their interactions in the file.

In writing your description, write about about the conceptual use cases, applications, logic, and component interactions instead of focusing on particular functions, variables, etc.
"""

DATA_STRUCTURES_FOUND_SYSTEM_PROMPT_JSON = """
You are an expert C programmer and a software engineering documentation expert. You write detailed documentation to explain code written in C.

You focus on writing technical documentation for data structures. You are skilled at explaining technical details as well as recognizing and articulating the key conceptual components and purpose of software.

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

Data structure to document:
"""

DATA_STRUCTURES_NONE_CONTENT = "\n---\nNo custom data structures defined in this file."


FUNCTIONS_FOUND_SYSTEM_PROMPT_JSON = """
You are an expert C programmer and a software engineering documentation expert. You write detailed documentation to explain code written in C.

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

FUNCTION_DECLS_FOUND_SYSTEM_PROMPT_JSON = """
You are an expert C programmer and a professional software documentation writer. Your task is to produce clear, \
precise documentation for public C APIs declared in header files. Your documentation helps developers understand how \
to use the API correctly and safely, without requiring any knowledge of its internal implementation.

You will be given both the function implementation code and the header file. Your documentation MUST be based \
**only on the public API interface as visible in the header file**. Use the implementation code ONLY to understand \
behavior relevant to API users (e.g., error handling, edge cases, parameter validation). \
**Do not expose or mention any implementation details.**

Your response must strictly follow this JSON schema:
{
    "single_sentence": "<short imperative sentence describing what the function does>",
    "description": "<paragraph explaining how and when to use the function, including preconditions, edge cases, and side effects>",
    "inputs": [
        {"name": "<parameter_name>", "content": "<what the parameter is, valid ranges, ownership expectations, and how invalid values are handled>"},
        ...
    ],
    "output": "<description of the return value or output behavior (e.g. mutation of input). Use 'None' if the function returns nothing and doesn't mutate any inputs>",
}

Guidelines:

- **Do not repeat the function name** in the `single_sentence` or `description`.
- The `single_sentence` must be a terse, imperative summary of the function's behavior (e.g., "Initializes a UART peripheral." or "Copies data to the destination buffer.").
- The `description` should:
    - Focus on the **purpose** of the function
    - Describe when and why to call it, what effect it has, and any relevant side effects
    - Include high-level **preconditions or expectations** (e.g., "must be called after initialization")
    - Avoid repeating specific parameter constraints or return value behavior; those belong in `inputs` and `output`
    - Use a single, well-structured paragraph. If needed, prefer clarity over verbosity.
- Each `input` must describe:
    - Purpose of the parameter
    - Allowed values or formats (e.g., ranges) when applicable
    - Ownership and nullability if applicable (e.g., "Must not be null", "Caller retains ownership")
    - How the function behaves on invalid input
- The `output` must describe:
    - The return value (if any) and what it means
    - If output is via pointers, describe what is written and under what conditions
    - Use `"None"` if the function has no return value and doesn't mutate by reference
- DO NOT mention:
    - Algorithms, data structures, or techniques used in the implementation
    - Private helper functions
    - Internal state or static variables
    - Code optimizations or performance tricks
- You may infer behavior that affects the caller (e.g., clamping values, error returns, thread safety) only if it's clearly visible in the implementation

Return ONLY the JSON according to the schema above. Do not use the format ```json ... ```, just return the JSON data.

"""
DECL_FOUND_USER_PROMPT = """
Document the public API for the function provided below.

Function to document:
"""

FUNCTIONS_FOUND_USER_PROMPT = """
Summarize the function in the code provided below. Describe the inputs, control flow and logic, and output.

- When describing a function, provide detail that matches the complexity of the function body. Large and complex functions should get longer explanations, while small ones much less.

Function to document:
"""

FUNCTIONS_NONE_CONTENT = (
    "\n---\nNo functions or function prototypes defined in this file."
)

VARIABLES_FOUND_SYSTEM_PROMPT_JSON = """
You are an expert C programmer and a software engineering documentation expert. You write detailed documentation to explain code written in C.

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


class CDeclarationRawSymbolCollection(RawSymbolCollection):
    data: dict[str, RawSymbolData]

    @classmethod
    def from_static_analysis(
        cls, code: str, root_rel_path: Path, reified_symbols: list[ReifiedSymbol] | None
    ) -> Self | None:
        declaration_raw_symbol_data = {}
        is_large_file = code_requires_multi_prompt(code)

        decl_symbols = [sym for sym in reified_symbols if sym.is_declaration]

        for reified_sym in decl_symbols:
            ts_symbol = reified_sym.raw
            # We skip declarations that weren't matched to definitions.
            # TODO should we still enumerate them without describing?
            if ts_symbol.name is not None and reified_sym.definition is not None:
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
                    reified_symbol=reified_sym,
                )
                declaration_raw_symbol_data[ts_symbol.name] = raw_symbol_data

        output = (
            None
            if len(declaration_raw_symbol_data) == 0
            else cls(data=declaration_raw_symbol_data)
        )
        return output

    @classmethod
    def from_llm(cls, code: str, root_rel_path: str) -> Self:
        raise NotImplementedError("Static analysis should be used for c decl")

    def to_dict(self) -> dict[str, RawSymbolData]:
        return self.data


class CFnDeclData(FnDeclData):
    @classmethod
    def system_prompt(cls, symbol: RawSymbolData) -> str:
        return (
            Prompt.empty()
            .append(Component(string=FUNCTION_DECLS_FOUND_SYSTEM_PROMPT_JSON))
            .append(GENERAL_STE_STYLE_INSTRUCTION)
            .append(USE_BACKTICKS_STYLE_INSTRUCTION)
            .into_str()
        )

    @classmethod
    def user_prompt(cls, symbol: RawSymbolData) -> str:
        symbol_body = symbol.reified_symbol.definition.raw.symbol_code
        user_prompt = (
            Prompt.empty()
            .append(NO_RESTATEMENT_STYLE_INSTRUCTION_FOR_SYMBOLS)
            .append(Component(string=f"{DECL_FOUND_USER_PROMPT}\n\n{symbol_body}"))
        )
        if symbol.file_code:
            user_prompt.append(
                Component(
                    string=f"\n\nAssociated header file code:\n\n{symbol.file_code}"
                )
            )
        return user_prompt.into_str()

    @classmethod
    def child_to_ir(cls, symbol: RawSymbolData) -> IrData | None:
        raise NotImplementedError("C declarations should not have children")

    @classmethod
    def child_to_field_name(cls, symbol: RawSymbolData) -> str:
        raise NotImplementedError("C declarations should not have children")


class CDeclarationCollection(IrCollection):
    data: dict[str, CFnDeclData | list[CFnDeclData]]

    @classmethod
    def from_llm(
        cls,
        llm: ChatOpenAI,
        symbols_list: RawSymbolCollection,
    ) -> Self:
        return cls.from_llm_with_ir_data(
            CFnDeclData,
            llm,
            symbols_list,
        )


class CIncludeRawSymbolCollection(RawSymbolCollection):
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
        raise NotImplementedError("Static analysis should be used for c imports")

    def to_dict(self) -> dict[str, RawSymbolData]:
        return self.data


class CDataStructureData(DataStructureData):
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
                    string=f"{DATA_STRUCTURES_FOUND_USER_PROMPT}{symbol.name}\n\nData structure code:\n\n{symbol.symbol_code}"
                )
            )
        )
        if symbol.file_code:
            user_prompt.append(
                Component(string=f"\n\nFull File code:\n\n{symbol.file_code}")
            )
        return user_prompt.into_str()

    @classmethod
    def child_to_ir(cls, symbol: RawSymbolData) -> IrData | None:
        raise NotImplementedError("C data structures should not have children")

    @classmethod
    def child_to_field_name(cls, symbol: RawSymbolData) -> str:
        raise NotImplementedError("C data structures should not have children")


class CDataStructureCollection(IrCollection):
    data: dict[str, CDataStructureData | list[CDataStructureData]]

    @classmethod
    def from_llm(cls, llm: ChatOpenAI, symbols_list: RawSymbolCollection) -> Self:
        return cls.from_llm_with_ir_data(CDataStructureData, llm, symbols_list)


class CFnData(FnData):
    @classmethod
    def system_prompt(cls, symbol: RawSymbolData) -> str:
        return (
            Prompt.empty()
            .append(Component(string=FUNCTIONS_FOUND_SYSTEM_PROMPT_JSON))
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
                    string=f"{FUNCTIONS_FOUND_USER_PROMPT}{symbol.name}\n\nFunction code:\n\n{symbol.symbol_code}"
                )
            )
        )
        if symbol.file_code:
            user_prompt.append(
                Component(string=f"\n\nFull File code:\n\n{symbol.file_code}")
            )
        return user_prompt.into_str()

    @classmethod
    def child_to_ir(cls, symbol: RawSymbolData) -> IrData | None:
        raise NotImplementedError("C functions should not have children")

    @classmethod
    def child_to_field_name(cls, symbol: RawSymbolData) -> str:
        raise NotImplementedError("C functions should not have children")


class CFunctionCollection(IrCollection):
    data: dict[str, CFnData | list[CFnData]]

    @classmethod  # Can add extra arg here with symbol table info
    def from_llm(cls, llm: ChatOpenAI, symbols_list: RawSymbolCollection) -> Self:
        return cls.from_llm_with_ir_data(CFnData, llm, symbols_list)


class CVariableData(VariableData):
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
            .append(Component(string=f"Variable code:\n\n{symbol.symbol_code}"))
        )
        if symbol.file_code:
            user_prompt.append(
                Component(string=f"\n\nFull File code:\n\n{symbol.file_code}")
            )
        return user_prompt.into_str()

    @classmethod
    def child_to_ir(cls, symbol: RawSymbolData) -> IrData | None:
        raise NotImplementedError("C variables should not have children")

    @classmethod
    def child_to_field_name(cls, symbol: RawSymbolData) -> str:
        raise NotImplementedError("C variables should not have children")


class CVariableCollection(IrCollection):
    data: dict[str, CVariableData | list[CVariableData]]

    @classmethod
    def from_llm(cls, llm: ChatOpenAI, symbols_list: RawSymbolCollection) -> Self:
        return cls.from_llm_with_ir_data(CVariableData, llm, symbols_list)


class CDataStructureRawSymbolCollection(RawSymbolCollection):
    data: dict[str, RawSymbolData]

    @classmethod
    def from_static_analysis(cls, code: str, root_rel_path: Path) -> Self | None:
        driver_tree = CppCDriverTree.from_code(code, root_rel_path)
        data_structure_raw_symbol_data = {}
        is_large_file = code_requires_multi_prompt(code)

        for ts_symbol in driver_tree.extract_data_structure_definitions():
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
                data_structure_raw_symbol_data[ts_symbol.name] = raw_symbol_data
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


class CFunctionRawSymbolCollection(RawSymbolCollection):
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
            ts_symbol = reified_sym.raw
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


class CVariableRawSymbolCollection(RawSymbolCollection):
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
