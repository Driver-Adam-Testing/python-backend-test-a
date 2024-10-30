from functools import partial
from pathlib import Path
from typing import Self

from utils.codemap_ctags import extract_symbols_w_ctags

# from .common import (
#     data_structure_dict_from_llm,
#     data_structure_dict_from_llm_multi_prompt,
#     fn_dict_from_llm,
#     fn_dict_from_llm_multi_prompt,
#     variables_dict_from_llm,
#     variables_dict_from_llm_multi_prompt,
# )
from .common_v2 import (
    IrCollection,
    IrData,
    NamedContent,
    RawSymbolCollection,
    RawSymbolData,
    SymbolKind,
    code_requires_multi_prompt,
    create_raw_symbol_via_ctags,
)

C_DATA_STRUCTURES = {"enum", "union", "struct", "typedef"}
C_FUNCTIONS = {"function", "prototype"}
C_MACROS = {"macro"}
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


class CDataStructureIrData(IrData):
    type: str
    members: list[NamedContent]
    description: str


class CDataStructureDict(IrCollection):
    data: dict[str, CDataStructureIrData | list[CDataStructureIrData]]


class CFunctionIrData(IrData):
    single_sentence: str
    inputs: list[NamedContent]
    control_flow: list[str]
    output: str


class CFunctionDict(IrCollection):
    data: dict[str, CFunctionIrData | list[CFunctionIrData]]


class CVariableIrData(IrData):
    type: str
    description: str
    use: str


class CVariableDict(IrCollection):
    data: dict[str, CVariableIrData | list[CVariableIrData]]


class CDataStructureRawSymbolCollection(RawSymbolCollection):
    data: dict[str, RawSymbolData]

    @classmethod
    def from_ctags(cls, code: str, root_rel_path: Path) -> Self | None:
        is_multi_prompt = code_requires_multi_prompt(code)

        symbols = extract_symbols_w_ctags(
            root_rel_path=root_rel_path,
            file_content=code,
        )

        data_structure_raw_symbol_data = {}
        for s in symbols:
            if s["kind"] in C_DATA_STRUCTURES:
                data_structure_raw_symbol_data[s["name"]] = create_raw_symbol_via_ctags(
                    ctags_symbol=s,
                    root_rel_path=root_rel_path,
                    code=code,
                    symbol_kind=SymbolKind.DATA_STRUCTURE,
                    ir_kind=CDataStructureIrData,
                    scope_relation=None,
                    delimiter=None,
                    is_multi_prompt=is_multi_prompt,
                )

        output = (
            None
            if len(data_structure_raw_symbol_data) == 0
            else cls(data=data_structure_raw_symbol_data)
        )
        return output

    @classmethod
    def from_ts(cls, code: str, root_rel_path: str) -> Self:
        pass

    def to_dict(self) -> dict[str, RawSymbolData]:
        return self.data


class CFunctionRawSymbolCollection(RawSymbolCollection):
    data: dict[str, RawSymbolData]

    @classmethod
    def from_ctags(cls, code: str, root_rel_path: Path) -> Self | None:
        is_multi_prompt = code_requires_multi_prompt(code)

        symbols = extract_symbols_w_ctags(
            root_rel_path=root_rel_path,
            file_content=code,
        )

        function_raw_symbol_data = {}
        for s in symbols:
            if s["kind"] in C_FUNCTIONS:
                function_raw_symbol_data[s["name"]] = create_raw_symbol_via_ctags(
                    ctags_symbol=s,
                    root_rel_path=root_rel_path,
                    code=code,
                    symbol_kind=SymbolKind.CALLABLE,
                    ir_kind=CFunctionIrData,
                    scope_relation=None,
                    delimiter=None,
                    is_multi_prompt=is_multi_prompt,
                )

        output = (
            None
            if len(function_raw_symbol_data) == 0
            else cls(data=function_raw_symbol_data)
        )
        return output

    @classmethod
    def from_ts(cls, code: str, root_rel_path: str) -> Self:
        pass

    def to_dict(self) -> dict[str, RawSymbolData]:
        return self.data


class CVariableRawSymbolCollection(RawSymbolCollection):
    data: dict[str, RawSymbolData]

    @classmethod
    def from_ctags(cls, code: str, root_rel_path: Path) -> Self | None:
        is_multi_prompt = code_requires_multi_prompt(code)

        symbols = extract_symbols_w_ctags(
            root_rel_path=root_rel_path,
            file_content=code,
        )

        variable_raw_symbol_data = {}
        for s in symbols:
            if s["kind"] in C_VARIABLES:
                variable_raw_symbol_data[s["name"]] = create_raw_symbol_via_ctags(
                    ctags_symbol=s,
                    root_rel_path=root_rel_path,
                    code=code,
                    symbol_kind=SymbolKind.VARIABLE,
                    ir_kind=CVariableIrData,
                    scope_relation=None,
                    delimiter=None,
                    is_multi_prompt=is_multi_prompt,
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


fn_dict_from_llm_c = partial(
    CFunctionDict.dict_from_llm,
    FUNCTIONS_FOUND_SYSTEM_PROMPT_JSON,
    FUNCTIONS_FOUND_USER_PROMPT,
    CFunctionIrData,
)

data_structure_dict_from_llm_c = partial(
    CDataStructureDict.dict_from_llm,
    DATA_STRUCTURES_FOUND_SYSTEM_PROMPT_JSON,
    DATA_STRUCTURES_FOUND_USER_PROMPT,
    CDataStructureIrData,
)

variable_dict_from_llm_c = partial(
    CVariableDict.dict_from_llm,
    VARIABLES_FOUND_SYSTEM_PROMPT_JSON,
    VARIABLES_FOUND_USER_PROMPT,
    CVariableIrData,
)
