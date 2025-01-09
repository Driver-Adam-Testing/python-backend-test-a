from pathlib import Path
from typing import Self

from utils.models import ChatOpenAI

from .ir_common import (
    FieldNameWithRawContent,
    FnData,
    IrCollection,
    IrData,
    ListedBacktickNameRawContentWithNone,
    ListedRawContentWithNone,
    NestedListedRawContent,
    VariableData,
)
from .symbol_common import (
    RawSymbolCollection,
    RawSymbolData,
    SymbolKind,
    default_ctags_analysis,
)

# GO for:
# Tasks and Functions
# Modules
# Constants
# Data Types (regs and nets)
# Ports


VERILOG_MODULES = {"module"}
VERILOG_FUNCTIONS_AND_TASKS = {"function", "task"}
VERILOG_DATA_TYPES = {"register", "net", "port"}
VERILOG_CONSTANTS = {"constant"}
VERILOG_PORTS = {"port"}

SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_VERILOG = """
You are an expert verilog programmer, experienced with hardware description languages and design, and a technical documentation expert. You write detailed documentation to explain code written in verilog.

You are skilled at explaining technical details as well as recognizing and articulating the key conceptual components and purpose of software.
"""

SOURCE_CODE_SMALL_SYSTEM_PROMPT_GENERAL_VERILOG = """
You are an expert verilog programmer, experienced with hardware description languages and design, and a technical documentation expert. You write detailed documentation to explain code written in verilog.

You are skilled at explaining technical details as well as recognizing and articulating the key conceptual components and purpose of software.

You specialize in effectively describing small and short source code files. Your goal is to be terse and clear, since the source code you are describing is small and simple.
"""

SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT = """
You will be given the content of a verilog source code file. In 1 or 2 paragraphs, explain the purpose of the file.

When writing your paragraphs, do not use speculative language.

When writing your paragraphs, consider questions like the following. You do not need to explicitly state these ideas, they are just given as examples of the kind of information to provide:

- Does this code provide narrow or broad functionality?
- What are the most important technical components?
- Is this code a collection of many different components? If so, what is the common theme or purpose?
- What kind of code is this? Does this largely define library components used elsewhere, top-level implementation, etc.?
"""

SOURCE_CODE_SMALL_PURPOSE_USER_PROMPT = """
You will be given the content of a verilog source code file. In a single paragraph of 3 to 5 sentences, explain the purpose of the file
"""

MODULES_FOUND_SYSTEM_PROMPT_JSON = """
You are an expert Verilog and hardware description language programmer and a technical documentation expert. You write detailed documentation to explain code written in Verilog.

You focus on writing technical documentation for modules. You are skilled at explaining technical details as well as recognizing and articulating the key conceptual components and purpose of software.

You will be given the name of a module to document and the source code where the module is defined.

When documenting control flow within the module, focus on logic blocks such as "always" blocks or "generate" blocks within the module.

Your job is to describe the module. **Always respond using exactly the following JSON schema**:
{
    "constants": [
        {"name": <constant1>, "content": <description of constant parameter 1>},
        {"name": <constant2>, "content": <description of constant parameter 2>},
        ...
    ],
    "ports": [
        {"name": <port_name1>, "content": <Terse 1 sentence description of the first port>},
        {"name": <port_name2>, "content": <Terse 1 sentence description of the second port>},
        ...
    ],
    "control_flow": [
        <bullet point 1 for description of logic and control flow>,
        <bullet point 2 for description of logic and control flow>,
        ...
    ],
    "description": <one paragraph description of the module>,
}

Return JSON according to the schema above. Do not use the format ```json ... ```, just return the JSON data.
"""

MODULES_FOUND_USER_PROMPT = """
Summarize the modules in the code provided below.

- A verilog module is a reusable block of verilog code that implements a specific functionality.
- A verilog module can embed other modules or be embedded in other modules.
- A verilog module may contain a list of parameter constants.
- A verilog module communicates through a list of input and output ports.
- When describing a module, provide detail that matches the complexity of the module. Large and complex modules should get longer explanations, while small ones a single sentence.

Module to document:
"""
# "logic_blocks": [
#     [
#         <bullet point 1 for description of logic and control flow of first logic block>,
#         <bullet point 2 for description of logic and control flow of first logic block>,
#         ...
#     ],
#     [
#         <bullet point 1 for description of logic and control flow of second logic block>,
#         <bullet point 2 for description of logic and control flow of second logic block>,
#         ...
#     ],
#     ...
# ]


FUNCTIONS_AND_TASKS_FOUND_SYSTEM_PROMPT_JSON = """
You are an expert Verilog and hardware description language programmer and a technical documentation expert. You write detailed documentation to explain code written in Verilog.

You focus on writing technical documentation for functions and tasks. You are skilled at explaining technical details as well as recognizing and articulating the key conceptual components and purpose of software.

You will be given the name of a functon or task to document and the source code where the module is defined.

In Verilog, a function processes a single input and returns a single value. A task is more general and can calculate multiple return values, returning them using `output` and `inout` type arguments.

Your job is to describe the function or task. **Always respond using exactly the following JSON schema**:
{
    "single_sentence": <terse single sentence description of the function or task>,
    "inputs": [
        {"name": <input_arg1>, "content": <description of input argument 1>},
        {"name": <input_arg2>, "content": <description of input argument 2>},
        ...
    ],
    "control_flow": [
        <bullet point 1 for description of logic and control flow>,
        <bullet point 2 for description of logic and control flow>,
        ...
    ],
    "outputs": [
        {"name": <output_arg1 or inout_arg1>, "content": <description of output or inout argument 1>},
        {"name": <output_arg2 or inout_arg2>, "content": <description of output or inout argument 2>},
    ]
}

Return JSON according to the schema above. Do not use the format ```json ... ```, just return the JSON data.
"""

FUNCTIONS_AND_TASKS_FOUND_USER_PROMPT = """
Summarize the functions and tasks in the code provided below.

- A verilog function processes a single input and returns a single value.
- A verilog task is more general and can calculate multiple return values, returning them using `output` and `inout` type arguments.
- When describing a function or task, provide detail that matches the complexity of the funciton or task. Large and complex functions or tasks should get longer explanations, while small ones a single sentence.

Function to document:
"""


DATA_TYPES_FOUND_SYSTEM_PROMPT_JSON = """
You are an expert Verilog and hardware description language programmer and a technical documentation expert. You write detailed documentation to explain code written in Verilog.

You focus on writing technical documentation for data types and data structures in verilog. You are skilled at explaining technical details as well as recognizing and articulating the key conceptual components and purpose of software.

You will be given the name of a data structure -- a port, a register, or a net data type -- to document and the source code where the port is defined.

Ports are signals that act as inputs and outputs between modules in verilog. Registers are variables to store values. Net data types represent values that change when some driver changes (e.g., a wire).

Your job is to describe the data type. **Always respond using exactly the following JSON schema**:
{
    "type": <type of the data type>,
    "description": <1 to 3 sentence description of the data type>,
    "use": <Terse 1 sentence description of how this data type is used>,
}

Return JSON according to the schema above. Do not use the format ```json ... ```, just return the JSON data.
"""

DATA_TYPES_FOUND_USER_PROMPT = """
Summarize the data types in the code provided below.

- Ports are signals that act as inputs and outputs between modules in verilog.
- Registers are variables to store values.
- Net data types represent values that change when some driver changes (e.g., a wire).
- When describing a data type, provide detail that matches the complexity of the data type. Large and complex data types should get longer explanations, while simpler ones much less.

Data type to document:
"""


# IR Classes
class VerilogModuleData(IrData):
    constants: ListedBacktickNameRawContentWithNone
    ports: ListedBacktickNameRawContentWithNone
    description: FieldNameWithRawContent
    control_flow: ListedRawContentWithNone
    # logic_blocks: NestedListedRawContent

    @classmethod
    def system_prompt(cls) -> str:
        return MODULES_FOUND_SYSTEM_PROMPT_JSON

    @classmethod
    def user_prompt(cls, symbol: RawSymbolData) -> str:
        user_prompt = f"{MODULES_FOUND_USER_PROMPT}{symbol.name}\n\nModule code:\n\n{symbol.symbol_code}"
        if symbol.file_code:
            user_prompt += f"\n\nFull File Code:\n\n{symbol.file_code}"
        return user_prompt

    @classmethod
    def child_to_ir(cls, symbol: RawSymbolData) -> type[IrData] | None:
        raise NotImplementedError("Modules should not have children")

    @classmethod
    def child_to_field_name(cls, child: RawSymbolData) -> str:
        raise NotImplementedError("Modules should not have children")

    @classmethod
    def default_instance(cls) -> Self:
        return cls(
            description=FieldNameWithRawContent(content=""),
            constants=ListedBacktickNameRawContentWithNone(content=[]),
            ports=ListedBacktickNameRawContentWithNone(content=[]),
            logic_blocks=NestedListedRawContent(content=[]),
        )


class VerilogModuleCollection(IrCollection):
    data: dict[str, VerilogModuleData | list[VerilogModuleData]]

    @classmethod
    def from_llm(cls, llm: ChatOpenAI, symbols_list: RawSymbolCollection) -> Self:
        return cls.from_llm_with_ir_data(VerilogModuleData, llm, symbols_list)


class VerilogFnTaskData(FnData):
    @classmethod
    def system_prompt(cls) -> str:
        return FUNCTIONS_AND_TASKS_FOUND_SYSTEM_PROMPT_JSON

    @classmethod
    def user_prompt(cls, symbol: RawSymbolData) -> str:
        user_prompt = f"{FUNCTIONS_AND_TASKS_FOUND_USER_PROMPT}{symbol.name}\n\nFunction or task code:\n\n{symbol.symbol_code}"
        if symbol.file_code:
            user_prompt += f"\n\nFull File Code:\n\n{symbol.file_code}"
        return user_prompt

    @classmethod
    def child_to_ir(cls, symbol: RawSymbolData) -> type[IrData] | None:
        raise NotImplementedError("Functions should not have children")

    @classmethod
    def child_to_field_name(cls, child: RawSymbolData) -> str:
        raise NotImplementedError("Functions should not have children")


class VerilogFnTaskCollection(IrCollection):
    data: dict[str, VerilogFnTaskData | list[VerilogFnTaskData]]

    @classmethod
    def from_llm(cls, llm: ChatOpenAI, symbols_list: RawSymbolCollection) -> Self:
        return cls.from_llm_with_ir_data(VerilogFnTaskData, llm, symbols_list)


class VerilogDataTypeData(VariableData):
    @classmethod
    def system_prompt(cls) -> str:
        return DATA_TYPES_FOUND_SYSTEM_PROMPT_JSON

    @classmethod
    def user_prompt(cls, symbol: RawSymbolData) -> str:
        user_prompt = f"{DATA_TYPES_FOUND_USER_PROMPT}{symbol.name}\n\nData type code:\n\n{symbol.symbol_code}"
        if symbol.file_code:
            user_prompt += f"\n\nFull File Code:\n\n{symbol.file_code}"
        return user_prompt

    @classmethod
    def child_to_ir(cls, symbol: RawSymbolData) -> type[IrData] | None:
        raise NotImplementedError("Data types should not have children")

    @classmethod
    def child_to_field_name(cls, child: RawSymbolData) -> str:
        raise NotImplementedError("Data types should not have children")


class VerilogDataTypeCollection(IrCollection):
    data: dict[str, VerilogDataTypeData | list[VerilogDataTypeData]]

    @classmethod
    def from_llm(cls, llm: ChatOpenAI, symbols_list: RawSymbolCollection) -> Self:
        return cls.from_llm_with_ir_data(VerilogDataTypeData, llm, symbols_list)


class VerilogModuleRawSymbolCollection(RawSymbolCollection):
    data: dict[str, RawSymbolData | list[RawSymbolData]]

    @classmethod
    def from_static_analysis(cls, code: str, root_rel_path: Path) -> Self:
        return default_ctags_analysis(
            collection_cls=cls,
            code=code,
            root_rel_path=root_rel_path,
            symbol_kind=SymbolKind.MODULE,
            ctags_kinds=VERILOG_MODULES,
            delimiter=None,
            add_symbol_padding=False,
        )

    @classmethod
    def from_llm(cls, code: str, root_rel_path: str) -> Self:
        raise NotImplementedError("Static analysis should be used for Verilog")

    def to_dict(self) -> dict[str, RawSymbolData]:
        return self.data


class VerilogFnTaskRawSymbolCollection(RawSymbolCollection):
    data: dict[str, RawSymbolData | list[RawSymbolData]]

    @classmethod
    def from_static_analysis(cls, code: str, root_rel_path: Path) -> Self:
        return default_ctags_analysis(
            collection_cls=cls,
            code=code,
            root_rel_path=root_rel_path,
            symbol_kind=SymbolKind.CALLABLE,
            ctags_kinds=VERILOG_FUNCTIONS_AND_TASKS,
            delimiter=None,
            add_symbol_padding=False,
        )

    @classmethod
    def from_llm(cls, code: str, root_rel_path: str) -> Self:
        raise NotImplementedError("Static analysis should be used for Verilog")

    def to_dict(self) -> dict[str, RawSymbolData]:
        return self.data


class VerilogDataTypeRawSymbolCollection(RawSymbolCollection):
    data: dict[str, RawSymbolData | list[RawSymbolData]]

    @classmethod
    def from_static_analysis(cls, code: str, root_rel_path: Path) -> Self:
        return default_ctags_analysis(
            collection_cls=cls,
            code=code,
            root_rel_path=root_rel_path,
            symbol_kind=SymbolKind.VARIABLE,
            ctags_kinds=VERILOG_DATA_TYPES,
            delimiter=None,
            add_symbol_padding=False,
        )

    @classmethod
    def from_llm(cls, code: str, root_rel_path: str) -> Self:
        raise NotImplementedError("Static analysis should be used for Verilog")

    def to_dict(self) -> dict[str, RawSymbolData]:
        return self.data
