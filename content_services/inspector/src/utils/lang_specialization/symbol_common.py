import abc
from enum import Enum, IntEnum, StrEnum, auto
from pathlib import Path
from typing import Self

from pydantic import BaseModel, Field
from utils.codemap_ctags import extract_symbols_w_ctags
from utils.models import ChatOpenAI

CHUNK_SIZE = 64_000
CHUNK_OVERLAP = 1_000
BLIND_ADVANCE_IF_NO_END_LINE = 200
BLIND_PADDING_TOP = 10
BLIND_PADDING_BOTTOM = 10


class Lang(IntEnum):
    C = 0
    CPP = 1
    HEADER = 2
    PYTHON = 3
    VERILOG = 4
    RUST = 5
    ASSEMBLY = 6
    JAVA = 7
    RUBY = 8
    C_SHARP = 9
    DEFAULT = 10

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
            case ".rb" | ".rbi":
                return cls.RUBY
            case ".cs":
                return cls.C_SHARP
            case _:
                return cls.DEFAULT


class ParserKind(Enum):
    UCTAGS = auto()
    TREE_SITTER = auto()
    LLM = auto()


class SymbolKind(Enum):
    VARIABLE = auto()
    CALLABLE = auto()
    DATA_STRUCTURE = auto()
    CLASS = auto()
    INTERFACE = auto()
    MODULE = auto()


class ScopeRelation(StrEnum):
    METHOD = "Methods"
    NESTED_CLASS = "Nested Classes"
    NESTED_INTERFACE = "Nested Interfaces"
    NESTED_DATA_STRUCTURE = "Nested Data Structures"
    FIELD = "Fields"
    CLASS_METHOD = "Class Methods"
    INSTANCE_METHOD = "Instance Methods"
    MODULE_METHOD = "Module Methods"
    ATTRIBUTE = "Attributes"
    ENUMERATOR = "Enumerators"


class RawSymbolData(BaseModel):
    parser_kind: ParserKind
    symbol_kind: SymbolKind
    name: str
    path: Path
    scope: str | None
    scope_relation: (
        ScopeRelation | None
    )  # this specifies the relation of the symbol to the scope, e.g. method, nested class, etc.
    children: list[Self]
    start_line: int | None
    end_line: int | None
    symbol_code: str | None
    file_code: str | None
    reference_code: str | None
    delimiter: str | None
    is_large_file: bool = Field(default=False)
    is_overloaded: bool = Field(default=False)


class RawSymbolCollection(BaseModel, abc.ABC):
    data: dict[str, RawSymbolData]

    @classmethod
    @abc.abstractmethod
    def from_static_analysis(cls, code: str, root_rel_path: Path) -> Self | None:
        pass

    @classmethod
    @abc.abstractmethod
    def from_llm(cls, code: str, root_rel_path: Path) -> Self | None:
        pass

    @abc.abstractmethod  # todo: unabstract this
    def to_dict(self) -> dict[str, RawSymbolData]:
        pass


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


def code_requires_multi_prompt(code: str) -> bool:
    from shared.chunking.text_splitter import split_text

    code_chunks = split_text(
        text=code,
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    return len(code_chunks) > 1


def create_raw_symbol_via_ctags(
    ctags_symbol: dict,
    root_rel_path: Path,
    code: str,
    symbol_kind: SymbolKind,
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
        name=ctags_symbol["name"],
        path=root_rel_path,
        scope=scope,
        scope_relation=scope_relation,
        children=[],
        start_line=ctags_symbol["line"],
        end_line=ctags_symbol.get(
            "end", ctags_symbol["line"] + BLIND_ADVANCE_IF_NO_END_LINE
        ),
        symbol_code=None,
        file_code=None,
        reference_code=None,
        delimiter=delimiter,
        is_large_file=is_multi_prompt,
        is_overloaded=is_overloaded,
    )

    if use_padding:
        start_line = max(0, raw_symbol_data.start_line - BLIND_PADDING_TOP)
        end_line = raw_symbol_data.end_line + BLIND_PADDING_BOTTOM
    else:
        start_line = raw_symbol_data.start_line
        end_line = raw_symbol_data.end_line
    s_code = "\n".join(code.split("\n")[start_line - 1 : end_line + 1])
    if is_multi_prompt or is_overloaded:
        s_code_chunks = split_text(
            text=s_code,
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
        )
        if len(s_code_chunks) > 1:
            raw_symbol_data.symbol_code = s_code_chunks[0].text
        else:
            raw_symbol_data.symbol_code = s_code
    else:
        raw_symbol_data.symbol_code = s_code
        raw_symbol_data.file_code = code

    return raw_symbol_data


def create_raw_symbol_via_llm(
    name: str,
    path: Path,
    code: str,
    symbol_kind: SymbolKind,
) -> RawSymbolData:
    return RawSymbolData(
        parser_kind=ParserKind.LLM,
        symbol_kind=symbol_kind,
        name=name,
        path=path,
        scope=None,
        scope_relation=None,
        children=[],
        start_line=None,
        end_line=None,
        symbol_code=code,
        file_code=code,
        reference_code=None,
        delimiter=None,
    )


def default_ctags_analysis(
    collection_cls: type[RawSymbolCollection],
    code: str,
    root_rel_path: Path,
    symbol_kind: SymbolKind,
    ctags_kinds: set[str],
    delimiter: str | None,
    add_symbol_padding: bool = False,
) -> RawSymbolCollection | None:
    is_multi_prompt = code_requires_multi_prompt(code)
    symbols = extract_symbols_w_ctags(root_rel_path=root_rel_path, file_content=code)

    raw_symbol_data = {}
    for s in symbols:
        if s["kind"] in ctags_kinds:
            raw_symbol_data[s["name"]] = create_raw_symbol_via_ctags(
                ctags_symbol=s,
                root_rel_path=root_rel_path,
                code=code,
                symbol_kind=symbol_kind,
                scope_relation=None,
                delimiter=delimiter,
                is_multi_prompt=is_multi_prompt,
                use_padding=add_symbol_padding,
            )

    output = None if len(raw_symbol_data) == 0 else collection_cls(data=raw_symbol_data)
    return output
