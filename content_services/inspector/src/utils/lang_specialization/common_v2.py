from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

import abc
from enum import Enum, IntEnum, auto
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


CHUNK_SIZE = 64_000
CHUNK_OVERLAP = 1_000


def code_requires_multi_prompt(code: str) -> bool:
    from shared.chunking.text_splitter import split_text

    code_chunks = split_text(
        text=code,
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    return len(code_chunks) > 1


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


BLIND_ADVANCE_IF_NO_END_LINE = 200
BLIND_PADDING_TOP = 100
BLIND_PADDING_BOTTOM = 100


def create_to_be_documented_raw_symbol_via_ctags(
    ctags_symbol: dict,
    root_rel_path: Path,
    code: str,
    symbol_kind: SymbolKind,
    ir_kind: type[IrData] | type[NestedIrData],
    scope_relation: str
    | None,  # scope relation should be the name of the field in the corresponding parent data class, e.g. "methods"
    delimiter: str | None,
    is_multi_prompt: bool,
    is_overloaded: bool = False,
    use_padding: bool = False,
) -> RawSymbolData:
    from shared.chunking.text_splitter import split_text

    if ctags_symbol.get("scope") is not None:
        scope = ctags_symbol["scope"].split(delimiter)[-1]
    else:
        scope = None

    raw_symbol_data = RawSymbolData(
        parser_kind=ParserKind.UCTAGS,
        symbol_kind=symbol_kind,
        ir_kind=ir_kind,
        name=ctags_symbol["name"],
        path=root_rel_path,
        scope=scope,
        scope_relation=scope_relation,
        children=[],
        start_line=ctags_symbol["line"],
        end_line=ctags_symbol.get(
            "end", ctags_symbol["line"] + BLIND_ADVANCE_IF_NO_END_LINE
        ),
        text=None,
        delimiter=delimiter,
    )
    if is_multi_prompt or is_overloaded:
        if use_padding:
            start_line = max(0, raw_symbol_data.start_line - BLIND_PADDING_TOP)
            end_line = raw_symbol_data.end_line + BLIND_PADDING_BOTTOM
        else:
            start_line = raw_symbol_data.start_line
            end_line = raw_symbol_data.end_line
        s_code = "\n".join(code.split("\n")[start_line - 1 : end_line + 1])
        s_code_chunks = split_text(
            text=s_code,
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
        )
        if len(s_code_chunks) > 1:
            raw_symbol_data.text = s_code_chunks[0].text
        else:
            raw_symbol_data.text = s_code
    else:
        raw_symbol_data.text = code

    return raw_symbol_data


def create_undocumented_raw_symbol_via_ctags(
    ctags_symbol: dict,
    root_rel_path: Path,
    symbol_kind: SymbolKind,
    scope_relation: str,
    delimiter: str | None,
) -> RawSymbolData:
    if ctags_symbol.get("scope") is not None:
        scope = ctags_symbol["scope"].split(delimiter)[-1]
    else:
        scope = None
    return RawSymbolData(
        parser_kind=ParserKind.UCTAGS,
        symbol_kind=symbol_kind,
        ir_kind=None,
        name=ctags_symbol["name"],
        path=root_rel_path,
        scope=scope,
        scope_relation=scope_relation,
        children=[],
        start_line=None,
        end_line=None,
        text=None,
        delimiter=delimiter,
    )


def snake_case_to_spaced_string(snake_case: str) -> str:
    split_str = snake_case.split("_")
    return " ".join(item.capitalize() for item in split_str)


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
    delimiter: str | None


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
        system_prompt: str,
        user_prompt: str,
        llm: ChatOpenAI,
        symbol: RawSymbolData,
    ) -> Self:
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
                if len(field_content) > 0:
                    output += f"- **{snake_case_to_spaced_string(field_name)}**: {field_content}\n"
            elif isinstance(field_content, list):
                if len(field_content) > 0:
                    output += f"- **{snake_case_to_spaced_string(field_name)}**:\n"
                    for item in field_content:
                        if isinstance(item, str):
                            output += f"    - {item}\n"
                        elif isinstance(item, NamedContent):
                            output += f"    - `{item.name}`: {item.content}\n"
                        else:
                            raise ValueError(
                                f"Unsupported item type in list: {type(item)}"
                            )
            else:
                raise ValueError(
                    f"Unsupported field content type: {type(field_content)}"
                )
        output += "\n"
        return output


class NestedIrData(BaseModel, abc.ABC):
    base_data: IrData  # all NestedIrData must have a base data field

    @classmethod
    @abc.abstractmethod
    def default_class(cls) -> Self:
        pass

    @classmethod
    def from_llm(
        cls,
        system_prompt: dict[str, str],
        user_prompt: dict[str, str],
        llm: ChatOpenAI,
        symbol: RawSymbolData,
    ) -> Self | None:
        data = cls.default_class().dict()

        # TODO: just pass the base_data IrData class in instead?
        type_hint_dict = get_type_hints(cls)
        base_data_cls = type_hint_dict["base_data"]

        # None on text means no context to pass to the LLM, so no base data will be generated
        # This can occur in C++ when a class is defined in a header, but some methods are defined in the source file
        if symbol.text is not None:
            data["base_data"] = base_data_cls.from_llm(
                llm=llm,
                system_prompt=system_prompt["base_data"],
                user_prompt=user_prompt["base_data"],
                symbol=symbol,
            )
        for child_symbol in symbol.children:
            if (
                child_symbol.scope_relation in type_hint_dict
            ):  # scope relation is defined on the child in the corresponding parser and must be equal to one of the fields in the data class
                if child_symbol.ir_kind is not None:
                    if child_symbol.scope_relation not in data:
                        data[child_symbol.scope_relation] = {}
                    if child_symbol.name not in data[child_symbol.scope_relation]:
                        scoped_name = child_symbol.name
                        if (
                            child_symbol.scope_relation is not None
                            and child_symbol.scope is not None
                        ):
                            scoped_name = f"{child_symbol.scope}{child_symbol.delimiter}{child_symbol.name}"
                        data[child_symbol.scope_relation][scoped_name] = []

                    data[child_symbol.scope_relation][scoped_name].append(
                        child_symbol.ir_kind.from_llm(
                            llm=llm,
                            system_prompt=system_prompt[child_symbol.scope_relation],
                            user_prompt=user_prompt[child_symbol.scope_relation],
                            symbol=child_symbol,
                        )
                    )
                else:  # assumed behavior - since no docs to be generated, just append to a list
                    if child_symbol.scope_relation not in data:
                        data[child_symbol.scope_relation] = []
                    data[child_symbol.scope_relation].append(child_symbol.name)
            else:
                raise ValueError(
                    f"Unsupported symbol {child_symbol.name} because it does not have a corresponding field in the data class of {child_symbol.scope_relation}"
                )

        return cls(**data)

    def render_markdown(self) -> str:
        output = ""

        # Base Data must be of type IrData, so we render it as is
        output += self.base_data.render_markdown()

        for field_name, field_content in self:
            if field_name != "base_data":
                if isinstance(field_content, list):
                    if len(field_content) > 0:
                        output += f"\n**{snake_case_to_spaced_string(field_name)}**\n"
                        for item in field_content:
                            output += f"    - {item}\n"
                elif isinstance(field_content, dict):
                    if len(field_content) > 0:
                        output += f"\n**{snake_case_to_spaced_string(field_name)}**\n"
                        for k, v in field_content.items():
                            if isinstance(v, list) and len(v) > 0:
                                for item in v:
                                    output += f"\n---\n#### {k}\n"
                                    output += item.render_markdown()
                            elif isinstance(v, IrData):
                                output += f"\n---\n#### {k}\n"
                                output += v.render_markdown()
                            # TODO: double nesting?
                            else:
                                raise ValueError(
                                    f"Unsupported type in field content dict: {type(v)}"
                                )
                else:
                    raise ValueError(
                        f"Unsupported type in field content: {type(field_content)}"
                    )
        return output


class IrCollection(BaseModel, abc.ABC):
    data: dict[str, IrData | NestedIrData]

    @classmethod
    def dict_from_llm(
        cls,
        system_prompt: str | dict[str, str],
        user_prompt: str | dict[str, str],
        data_cls: type[IrData],
        llm: ChatOpenAI,
        symbols_list: RawSymbolCollection,
    ) -> Self:
        symbols_dict = {}
        for _, s in symbols_list.data.items():
            if isinstance(s, list):
                for item in s:
                    if item.name not in symbols_dict:
                        symbols_dict[item.name] = []
                    symbols_dict[item.name].append(
                        data_cls.from_llm(
                            system_prompt=system_prompt,
                            user_prompt=user_prompt,
                            llm=llm,
                            symbol=item,
                        )
                    )
            elif isinstance(s, RawSymbolData):
                if s.name not in symbols_dict:
                    symbols_dict[s.name] = []
                symbols_dict[s.name].append(
                    data_cls.from_llm(
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                        llm=llm,
                        symbol=s,
                    )
                )
        return cls(data=symbols_dict)

    def render_markdown(self) -> str:
        output = ""
        for k, v in self.data.items():
            for item in v:
                output += f"\n---\n### {k}\n"
                output += item.render_markdown()

        return output

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
    description: str
    type: str | None
    members: list[NamedContent]
    inherits_from: list[str]


class ClassData(NestedIrData):
    base_data: ClassBaseData
    methods: dict[str, list[FnData]]
    nested_classes: list[str]

    @classmethod
    def default_class(cls) -> Self:
        base_data = ClassBaseData(
            type="", members=[], description="Implemented elsewhere", inherits_from=[]
        )
        return cls(base_data=base_data, methods={}, nested_classes=[])


class ClassDict(IrCollection):
    data: dict[str, list[ClassData]]
