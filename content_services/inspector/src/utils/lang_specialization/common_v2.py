from __future__ import annotations

import abc
from enum import Enum, IntEnum, auto
from pathlib import Path
from typing import Self, get_type_hints

import openai
from pydantic import BaseModel
from utils.models import ChatOpenAI, OutputConfig, OutputConfigKind


class Lang(IntEnum):
    C = 0
    CPP = 1
    HEADER = 2
    PYTHON = 3
    VERILOG = 4
    RUST = 5
    ASSEMBLY = 6
    JAVA = 7
    DEFAULT = 8

    @classmethod
    def from_ext_and_source(cls, ext: str, source: str) -> Self:
        match ext:
            case ".c":
                return cls.C
            case ".cpp" | ".cc" | ".cxx" | ".c++":
                return cls.CPP
            case ".h" | ".hpp" | ".hh" | ".hxx" | ".h++":
                return cls.HEADER
            case ".py" | ".pyw" | ".pyi":
                return cls.PYTHON
            case ".v" | ".sv":  # TODO: seprately specialize SystemVerilog
                return cls.VERILOG
            case ".rs":
                return cls.RUST
            case ".s" | ".S" | ".asm" | ".nasm" | ".inc":
                return cls.ASSEMBLY
            case ".java":
                return cls.JAVA
            case _:
                return cls.DEFAULT


def _disambiguate_header(source: str, fallback: Lang) -> Lang:
    llm = ChatOpenAI(model="gpt-4o-2024-08-06", temperature=0, request_timeout=120)
    system_prompt = """
    You are a software engineering expert that determines whether a header file corresponds to the C or C++ language.

    Header files ('.h' extension) are used both in C and C++. You will be given source code from a header file and will answer whether it corresponds to C or C++ code.

    You will be given the source code in the following format:

    File contents:

    <file_contents>

    You only respond with a single number to indicate your response:
    - 0 if the code corresponds to C
    - 1 if the code corresponds to C++
    """
    user_prompt = f"File contents:\n\n{source}"
    c_or_cpp_raw = llm.generate_response(
        system_prompt=system_prompt, user_prompt=user_prompt
    )
    try:
        zero_or_one = int(c_or_cpp_raw)
        match zero_or_one:
            case 0:
                return Lang.C
            case 1:
                return Lang.CPP
            case _:
                return fallback
    except ValueError as e:
        print(
            f"Failed to parse integer from LLM response to determine if a header file is C or C++: {e}"
        )
        return fallback


def snake_case_to_spaced_string(snake_case: str) -> str:
    return snake_case.replace("_", " ").capitalize()


class ParserKind(Enum):
    UCTAGS = auto()
    TREE_SITTER = auto()


class SymbolKind(Enum):
    VARIABLE = auto()
    CALLABLE = auto()
    DATA_STRUCTURE = auto()


class RawSymbolData(BaseModel):
    parser_kind: ParserKind
    symbol_kind: SymbolKind
    ir_kind: type[IrData] | type[NestedIrData] | None
    name: str
    path: Path
    scope: str | None
    scope_relation: (
        str | None
    )  # this specifies the relation of the symbol to the scope, e.g. method, nested class, etc.
    children: list[Self] | None
    start_line: int | None
    end_line: int | None
    text: (
        str | None
    )  # If text is None - indicates something like a class that is implemented in another file but has methods implemented in this file


class RawSymbolCollection(BaseModel, abc.ABC):
    @classmethod
    @abc.abstractmethod
    def from_ctags(cls, code: str, root_rel_path: Path) -> Self | None:
        pass

    @classmethod
    @abc.abstractmethod
    def from_ts(cls, code: str, root_rel_path: Path) -> Self | None:
        pass

    @abc.abstractmethod
    def to_dict(self) -> dict[str, RawSymbolData]:
        pass


class NamedContent(BaseModel):
    name: str
    content: str


class ListData(BaseModel):
    data: list[str]

    @classmethod
    def from_llm(
        cls, llm: ChatOpenAI, system_prompt: str, user_prompt: str, code: str
    ) -> Self:
        user_prompt_complete = f"{user_prompt}\n\nCode:\n\n{code}"
        content_raw = llm.generate_response(
            system_prompt=system_prompt,
            user_prompt=user_prompt_complete,
            output_cfg=OutputConfig(kind=OutputConfigKind.JSON_STRICT, payload=cls),
        )

        return cls.parse_raw(content_raw)

    def render_markdown(self) -> str:
        output = ""
        output += "\n---\n"
        for dep in self.data:
            output += f"- `{dep}`\n"
        output += "\n"
        return output

    def __str__(self) -> str:
        return self.render_markdown()


class IrData(BaseModel, abc.ABC):
    @classmethod
    def from_llm(
        cls,
        llm: ChatOpenAI,
        system_prompt: str,
        user_prompt: str,
        symbol: RawSymbolData,
    ) -> Self:
        if symbol.text is None:
            return cls()
        user_prompt_complete = f"{user_prompt} {symbol.name}\n\nCode:\n\n{symbol.text}"
        try:
            content_raw = llm.generate_response(
                system_prompt=system_prompt,
                user_prompt=user_prompt_complete,
                output_cfg=OutputConfig(kind=OutputConfigKind.JSON_STRICT, payload=cls),
            )
        except openai.LengthFinishReasonError as _:
            print("LengthFinishReasonError caught")
            return None

        return cls.parse_raw(content_raw)

    def render_markdown(self) -> str:
        output = ""
        for field_name, field_content in self:
            if isinstance(field_content, str):
                output += f"- **{snake_case_to_spaced_string(field_name)}**: {field_content}\n"
            elif isinstance(field_content, list):
                output += f"- **{snake_case_to_spaced_string(field_name)}**:\n"
                for item in field_content:
                    if isinstance(item, str):
                        output += f"    - {item}\n"
                    elif isinstance(item, NamedContent):
                        output += f"    - `{item.name}`: {item.content}\n"
                    else:
                        raise ValueError(f"Unsupported item type in list: {type(item)}")
            else:
                raise ValueError(
                    f"Unsupported field content type: {type(field_content)}"
                )
        output += "\n"
        return output


class NestedIrData(BaseModel, abc.ABC):
    base_data: IrData  # all nested data should have a base data field

    @classmethod
    def from_llm(
        cls,
        llm: ChatOpenAI,
        system_prompts: dict[str, str],
        user_prompts: dict[str, str],
        symbol: RawSymbolData,
    ) -> Self | None:
        data = {}

        # TODO: undefined class in file
        data["base_data"] = cls.base_data.from_llm(
            llm=llm,
            system_prompt=system_prompts["base_data"],
            user_prompt=user_prompts["base_data"],
            symbol=symbol,
        )
        type_hint_dict = get_type_hints(cls)
        for child_symbol in symbol.children:
            if (
                child_symbol.scope_relation in type_hint_dict
            ):  # scope relation is defined in the corresponding parser
                # TODO: maybe just check if the ir_kind is None?
                if isinstance(type_hint_dict[child_symbol.scope_relation], dict):
                    data[child_symbol.scope_relation][child_symbol.name].append(
                        child_symbol.ir_kind.from_llm(
                            llm=llm,
                            system_prompt=system_prompts[child_symbol.scope_relation],
                            user_prompt=user_prompts[child_symbol.scope_relation],
                            symbol=child_symbol,
                        )
                    )
                elif isinstance(type_hint_dict[child_symbol.scope_relation], list):
                    data[child_symbol.scope_relation].append(child_symbol.name)
            else:
                print(
                    f"Skipping symbol {child_symbol.name} because it does not have a corresponding field in the data class"
                )

        return cls(data=data)

    def render_markdown(self) -> str:
        output = ""

        # Base Data must be of type IrData, so we render it as is
        output += self.base_data.render_markdown()

        for field_name, field_content in self:
            if field_name != "base_data":
                output += f"\n**{field_name}**\n"
                if isinstance(field_content, list):
                    for item in field_content:
                        output += f"    - {item}\n"
                elif isinstance(field_content, dict):
                    # The dict case should be of the form {str: IrData | list[IrData]}
                    for k, v in field_content.items():
                        if isinstance(v, list):
                            for item in v:
                                output += f"\n---\n#### {k}\n"
                                output += item.render_markdown()
                        elif isinstance(v, IrData):
                            output += f"\n---\n#### {k}\n"
                            output += v.render_markdown()
                        else:
                            raise ValueError(f"Unsupported type in dict: {type(v)}")
                else:
                    raise ValueError(
                        f"Unsupported type in field content: {type(field_content)}"
                    )
        return output


class IrCollection(BaseModel, abc.ABC):
    data: dict[str, type[IrData] | type[NestedIrData]]

    @classmethod
    def dict_from_llm(
        cls,
        llm: ChatOpenAI,
        system_prompt: str,
        user_prompt: str,
        symbols_list: list[type[RawSymbolData]],
        data_cls: type[IrData],
    ) -> Self:
        symbols_dict = {
            s: data_cls.from_llm(
                llm=llm,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                symbol=s,
            )
            for s in symbols_list
        }
        return cls(data=symbols_dict)

    def render_markdown(self) -> str:
        output = ""
        for k, v in self.data.items():
            output += f"\n---\n### {k}\n"
            output += v.render_markdown()

    def __str__(self) -> str:
        return self.render_markdown()


# -------------------------------------------------------------------------- #
#                    Language Specialization Logic                           #
#                                                                            #
# - The following classes are defaults, but a new language can be            #
#   specialized by creating new classes that inherit from IrData or          #
#   NestedIrData and adding the fields of interest. A corresponding Dict     #
#   class will also need to be made.                                         #
# - A note on the Data classes: the fields in the classes should be order by #
#   how you want them to be documented. Also note that only specific types   #
#   are supported.                                                           #
# -------------------------------------------------------------------------- #
class VariableData(IrData):
    type: str
    description: str
    use: str


class VariableDict(IrCollection):
    data: dict[str, list[VariableData]]


class DataStructureData(IrData):
    type: str
    members: list[NamedContent]
    description: str


class DataStructureDict(IrCollection):
    data: dict[str, list[DataStructureData]]


class FnData(IrData):
    single_sentence: str
    inputs: list[NamedContent]
    control_flow: list[str]
    output: str


class FnDict(IrCollection):
    data: dict[str, list[FnData]]


class ClassBaseData(IrData):
    type: str | None
    members: list[NamedContent]
    description: str
    inherits_from: list[str]


class ClassData(NestedIrData):
    base_data: ClassBaseData
    methods: dict[str, list[FnData]]
    nested_classes: list[str]


class ClassDict(IrCollection):
    data: dict[str, list[ClassData]]
