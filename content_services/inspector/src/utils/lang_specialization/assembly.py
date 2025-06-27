from pathlib import Path
from typing import Self

from utils.models import ChatOpenAI

from .default import (
    default_llm_analysis,
)
from .ir_common import (
    DataStructureData,
    FnData,
    IrCollection,
    IrData,
    VariableData,
)
from .symbol_common import RawSymbolCollection, RawSymbolData, SymbolKind

SOURCE_CODE_SYSTEM_PROMPT_GENERAL_DEFAULT = """
You are an assembly software engineering documentation expert. You write detailed documentation to explain software.

You are skilled at explaining technical details as well as recognizing and articulating the key conceptual components and purpose of software.
"""

SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT = """
You will be given the content of an assembly source code file. In 1 to 3 paragraphs, explain the purpose of the file.

When writing your paragraphs, do not use speculative language.

When writing your paragraphs, consider questions like the following. You do not need to explicitly state these ideas, they are just given as examples of the kind of information to provide:

- Does this code provide narrow or broad functionality?
- What are the most important technical components?
- Is this code a collection of many different components? If so, what is the common theme or purpose?
"""

SOURCE_CODE_SMALL_PURPOSE_USER_PROMPT = """
You will be given the content of a source code file. In a single paragraph of 3 to 5 sentences, explain the purpose of the file. Consider questions such as the following when providing your output:

- Does this code provide narrow or broad functionality?
- What are the most important technical components?
"""

IMPORTS_SYSTEM_PROMPT_JSON = """
Identify and list the imports and dependencies used in the code provided below.

You only respond with a list of imports and dependencies. **Always respond using exactly the following JSON schema**:
{
    "data": [
        <import1_name>,
        <import2_name>,
        ...
    ]
}

If there are no imports or dependencies return an empty array.
"""


DATA_STRUCTURES_CHECKER_SYSTEM_PROMPT_JSON = """
Your job is to list any important data structures defined in the assembly code provided below.

- A data structure is custom or compound type in a the assembly language, specifically structs. Functions, macros, and variables are not data structures.

You only respond with a list of data structures. **Always respond using exactly the following JSON schema**:
{
    "data": [
        <name of first data structure>,
        <name of second data structure>,
        ...
    ]
}

If there are no data structures return an empty array.
"""

DATA_STRUCTURES_FOUND_SYSTEM_PROMPT_JSON = """
You are an expert programmer and an assembly software engineering documentation expert. You write detailed documentation to explain code.

You focus on writing technical documentation for data structures. You are skilled at explaining technical details as well as recognizing and articulating the key conceptual components and purpose of software.

You will be given the name of a data structure to document and the assembly source code where the data structure is defined.

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


FUNCTIONS_CHECKER_SYSTEM_PROMPT_JSON = """
Your job is to list any functions, subroutines or procedures defined in the assembly code provided below.

- You are only looking for functions, subroutines or procedures that are **fully defined and implemented** in the code given to you. That is, the implementation of the function is in the source code given to you.
- do not consider macros as a function, subroutine, or procedure.
- functions with the same name but one has a leading _ are the same function, only list one of these functions.

You only respond with a list of functions, subroutines, and procedures. **Always respond using exactly the following JSON schema**:
{
    "data": [
        <name of first function/subroutine/procedure>,
        <name of second function/subroutine/procedure>,
        ...
    ]
}

If there are no functions return an empty array.
"""

FUNCTIONS_FOUND_SYSTEM_PROMPT_JSON = """
You are an expert programmer and an assembly software engineering documentation expert. You write detailed documentation to explain code.

You focus on writing technical documentation for functions, subroutines and procedures. You are skilled at explaining technical details as well as recognizing and articulating the key conceptual components and purpose of software.

You will be given the name of a function to document and the assembly source code where the function is defined.

Your job is to describe the function, subroutine or procedure. **Always respond using exactly the following JSON schema**:
{
    "single_sentence": <terse single sentence description of the function, subroutine, or procedure>,
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
Summarize the function, subroutine or procedure in the code provided below. Describe the inputs, control flow and logic, and output.

- When describing a function/subroutine/procedure, provide detail that matches the complexity of the body. Large and complex functions should get longer explanations, while small ones much less.

Function/Subroutine/Procedure to document:
"""


MACRO_CHECKER_SYSTEM_PROMPT_JSON = """
Your job is to list any macros defined in the assembly code provided below.

- You are only looking for macros that are defined in the code given to you.

You only respond with a list of macros. **Always respond using exactly the following JSON schema**:
{
    "data": [
        <name of first macro>,
        <name of second macro>,
        ...
    ]
}

If there are no macros return an empty array.
"""

MACRO_FOUND_SYSTEM_PROMPT_JSON = """
You are an expert programmer and an assembly software engineering documentation expert. You write detailed documentation to explain code.

You focus on writing technical documentation for macros. You are skilled at explaining technical details as well as recognizing and articulating the key conceptual components and purpose of software.

You will be given the name of a macro to document and the assembly source code where the macro is defined.

Your job is to describe the macro. **Always respond using exactly the following JSON schema**:
{
    "single_sentence": <terse single sentence description of the macro>,
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

MACRO_FOUND_USER_PROMPT = """
Summarize the macro in the code provided below. Describe the inputs, control flow and logic, and output.

- When describing a macro, provide detail that matches the complexity of the body. Large and complex macros should get longer explanations, while small ones much less.

Macro to document:
"""


VARIABLES_CHECKER_SYSTEM_PROMPT_JSON = """
Your job is to list any global variables defined in the assembly code provided below.

- A global variable could be declared in the data or bss sections if present. Local variables declared and used inside of subroutines or other scopes are not global variables. Only include global variables.

**You only include the name of any global variable**, not its value or contents.
You only respond with a list of global variable names. **Always respond using exactly the following JSON schema**:
{
    "data": [
        <name of first global variable>,
        <name of second global variable>,
        ...
    ]
}

If there are no global variables return an empty array.
"""

VARIABLES_FOUND_SYSTEM_PROMPT_JSON = """
You are an expert programmer and an assembly software engineering documentation expert. You write detailed documentation to explain code.

You focus on writing technical documentation for variables. You are skilled at explaining technical details as well as recognizing and articulating the key conceptual components and purpose of software.

You will be given the name of a variable to document and the source code where the data structure is defined.

Your job is to describe the variable. **Always respond using exactly the following JSON schema**:
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
class AssemblyDataStructureRawSymbolCollection(RawSymbolCollection):
    data: dict[str, RawSymbolData]

    @classmethod
    def from_static_analysis(cls, code: str, root_rel_path: Path) -> Self | None:
        raise NotImplementedError("Assembly parsing uses llm extraction")

    @classmethod
    def from_llm(cls, llm: ChatOpenAI, code: str, root_rel_path: str) -> Self | None:
        return default_llm_analysis(
            collection_cls=cls,
            llm=llm,
            code=code,
            root_rel_path=root_rel_path,
            system_prompt=DATA_STRUCTURES_CHECKER_SYSTEM_PROMPT_JSON,
            user_prompt="",
            symbol_kind=SymbolKind.DATA_STRUCTURE,
        )

    def to_dict(self) -> dict[str, RawSymbolData]:
        return self.data


class AssemblySubroutineRawSymbolCollection(RawSymbolCollection):
    data: dict[str, RawSymbolData]

    @classmethod
    def from_static_analysis(cls, code: str, root_rel_path: Path) -> Self | None:
        raise NotImplementedError("Assembly parsing uses llm extraction")

    @classmethod
    def from_llm(cls, llm: ChatOpenAI, code: str, root_rel_path: str) -> Self | None:
        return default_llm_analysis(
            collection_cls=cls,
            llm=llm,
            code=code,
            root_rel_path=root_rel_path,
            system_prompt=FUNCTIONS_CHECKER_SYSTEM_PROMPT_JSON,
            user_prompt="",
            symbol_kind=SymbolKind.CALLABLE,
        )

    def to_dict(self) -> dict[str, RawSymbolData]:
        return self.data


class AssemblyMacroRawSymbolCollection(RawSymbolCollection):
    data: dict[str, RawSymbolData]

    @classmethod
    def from_static_analysis(cls, code: str, root_rel_path: Path) -> Self | None:
        raise NotImplementedError("Assembly parsing uses llm extraction")

    @classmethod
    def from_llm(cls, llm: ChatOpenAI, code: str, root_rel_path: str) -> Self | None:
        return default_llm_analysis(
            collection_cls=cls,
            llm=llm,
            code=code,
            root_rel_path=root_rel_path,
            system_prompt=MACRO_CHECKER_SYSTEM_PROMPT_JSON,
            user_prompt="",
            symbol_kind=SymbolKind.CALLABLE,
        )

    def to_dict(self) -> dict[str, RawSymbolData]:
        return self.data


class AssemblyVariableRawSymbolCollection(RawSymbolCollection):
    data: dict[str, RawSymbolData]

    @classmethod
    def from_static_analysis(cls, code: str, root_rel_path: Path) -> Self | None:
        raise NotImplementedError("Assembly parsing uses llm extraction")

    @classmethod
    def from_llm(cls, llm: ChatOpenAI, code: str, root_rel_path: str) -> Self | None:
        return default_llm_analysis(
            collection_cls=cls,
            llm=llm,
            code=code,
            root_rel_path=root_rel_path,
            system_prompt=VARIABLES_CHECKER_SYSTEM_PROMPT_JSON,
            user_prompt="",
            symbol_kind=SymbolKind.VARIABLE,
        )

    def to_dict(self) -> dict[str, RawSymbolData]:
        return self.data


# IR Classes
class AssemblyDataStructureData(DataStructureData):
    @classmethod
    def system_prompt(cls, symbol: RawSymbolData) -> str:
        return DATA_STRUCTURES_FOUND_SYSTEM_PROMPT_JSON

    @classmethod
    def user_prompt(cls, symbol: RawSymbolData) -> str:
        return f"{DATA_STRUCTURES_FOUND_USER_PROMPT}{symbol.name}\n\nCode:\n\n{symbol.file_code}"

    @classmethod
    def child_to_ir(cls, symbol: RawSymbolData) -> type[IrData] | None:
        raise NotImplementedError("Assembly data structures should not have children")

    @classmethod
    def child_to_field_name(cls, child: RawSymbolData) -> str:
        raise NotImplementedError("Assembly data structures should not have children")


class AssemblyDataStructureCollection(IrCollection):
    data: dict[str, AssemblyDataStructureData | list[AssemblyDataStructureData]]

    @classmethod
    def from_llm(cls, llm: ChatOpenAI, symbols_list: RawSymbolCollection) -> Self:
        return cls.from_llm_with_ir_data(AssemblyDataStructureData, llm, symbols_list)


class AssemblySubroutineData(FnData):
    @classmethod
    def system_prompt(cls, symbol: RawSymbolData) -> str:
        return FUNCTIONS_FOUND_SYSTEM_PROMPT_JSON

    @classmethod
    def user_prompt(cls, symbol: RawSymbolData) -> str:
        return (
            f"{FUNCTIONS_FOUND_USER_PROMPT}{symbol.name}\n\nCode:\n\n{symbol.file_code}"
        )

    @classmethod
    def child_to_ir(cls, symbol: RawSymbolData) -> type[IrData] | None:
        raise NotImplementedError("Assembly functions should not have children")

    @classmethod
    def child_to_field_name(cls, child: RawSymbolData) -> str:
        raise NotImplementedError("Assembly functions should not have children")


class AssemblySubroutineCollection(IrCollection):
    data: dict[str, AssemblySubroutineData | list[AssemblySubroutineData]]

    @classmethod
    def from_llm(cls, llm: ChatOpenAI, symbols_list: RawSymbolCollection) -> Self:
        return cls.from_llm_with_ir_data(AssemblySubroutineData, llm, symbols_list)


class AssemblyMacroData(FnData):
    @classmethod
    def system_prompt(cls, symbol: RawSymbolData) -> str:
        return MACRO_FOUND_SYSTEM_PROMPT_JSON

    @classmethod
    def user_prompt(cls, symbol: RawSymbolData) -> str:
        return f"{MACRO_FOUND_USER_PROMPT}{symbol.name}\n\nCode:\n\n{symbol.file_code}"

    @classmethod
    def child_to_ir(cls, symbol: RawSymbolData) -> type[IrData] | None:
        raise NotImplementedError("Assembly macros should not have children")

    @classmethod
    def child_to_field_name(cls, child: RawSymbolData) -> str:
        raise NotImplementedError("Assembly macros should not have children")


class AssemblyMacroCollection(IrCollection):
    data: dict[str, AssemblyMacroData | list[AssemblyMacroData]]

    @classmethod
    def from_llm(cls, llm: ChatOpenAI, symbols_list: RawSymbolCollection) -> Self:
        return cls.from_llm_with_ir_data(AssemblyMacroData, llm, symbols_list)


class AssemblyVariableData(VariableData):
    @classmethod
    def system_prompt(cls, symbol: RawSymbolData) -> str:
        return VARIABLES_FOUND_SYSTEM_PROMPT_JSON

    @classmethod
    def user_prompt(cls, symbol: RawSymbolData) -> str:
        return (
            f"{VARIABLES_FOUND_USER_PROMPT}{symbol.name}\n\nCode:\n\n{symbol.file_code}"
        )

    @classmethod
    def child_to_ir(cls, symbol: RawSymbolData) -> type[IrData] | None:
        raise NotImplementedError("Assembly variables should not have children")

    @classmethod
    def child_to_field_name(cls, child: RawSymbolData) -> str:
        raise NotImplementedError("Assembly variables should not have children")


class AssemblyVariableCollection(IrCollection):
    data: dict[str, AssemblyVariableData | list[AssemblyVariableData]]

    @classmethod
    def from_llm(cls, llm: ChatOpenAI, symbols_list: RawSymbolCollection) -> Self:
        return cls.from_llm_with_ir_data(AssemblyVariableData, llm, symbols_list)
