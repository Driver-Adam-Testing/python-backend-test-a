import abc
import textwrap
from dataclasses import dataclass, field
from enum import Enum, IntEnum, StrEnum, auto
from pathlib import Path
from typing import Self

from openai import OpenAIError
from pydantic import BaseModel, Field
from utils.codemap_ctags import extract_symbols_w_ctags
from utils.models import ChatOpenAI

CHUNK_SIZE = 64_000
CHUNK_OVERLAP = 1_000
BLIND_ADVANCE_IF_NO_END_LINE = 200
BLIND_PADDING_TOP = 100
BLIND_PADDING_BOTTOM = 10


class Lang(IntEnum):
    C = 0
    CPP = 1
    C_OR_CPP_HEADER = 2
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
                return cls.C_OR_CPP_HEADER
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

    def __str__(self) -> str:
        return self.name


class ParserKind(Enum):
    UCTAGS = auto()
    TREE_SITTER = auto()
    LLM = auto()


class SymbolKind(Enum):
    VARIABLE = auto()
    CALLABLE = auto()
    CALLABLE_DECLARATION = auto()
    CALL = auto()
    DATA_STRUCTURE = auto()
    DATA_STRUCTURE_INSTANCE = auto()
    CLASS = auto()
    INTERFACE = auto()
    MODULE = auto()
    IMPORT = auto()


class ScopeRelation(StrEnum):
    # This represents the relationship of a child symbol
    # to its parent (scope), e.g. it is a METHOD of the parent class
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


class RawTreeSitterSymbolData(BaseModel):
    name: str | None
    start_line: int
    end_line: int
    start_byte: int
    end_byte: int
    file_path: Path
    symbol_kind: SymbolKind
    fully_qualified_parent_path: str | None = (
        None  # this could be a nested namespace as well. Does nullable make sense here? Is global scope None?
    )
    symbol_code: (
        None | str
    )  # TODO: this is somewhat a hack since we need the code, but makes symbols bulky

    class Config:
        """
        This gives us __hash__!
        """

        frozen = True


@dataclass(frozen=True)
class ReifiedSymbol:
    """
    Extends LinkedSymbol with a list of usages (if this is a definition).
    """

    raw: RawTreeSitterSymbolData
    is_definition: bool
    is_declaration: bool
    definition: Self | None = None
    usages: list[Self] = field(default_factory=list)
    calls: list[Self] = field(default_factory=list)
    declarations: list[Self] = field(
        default_factory=list
    )  # Should this be a list? Likely not
    parent: Self | None = None


class RawSymbolData(BaseModel):
    parser_kind: ParserKind
    symbol_kind: SymbolKind
    name: str
    path: Path
    scope: str | None
    scope_relation: ScopeRelation | None
    children: list[Self]
    start_line: int | None
    end_line: int | None
    symbol_code: str | None
    file_code: str | None
    reference_code: str | None
    delimiter: str | None
    is_large_file: bool = Field(default=False)
    is_overloaded: bool = Field(default=False)

    # TODO kind of hack to put on here, but just cranking for now
    reified_symbol: ReifiedSymbol | None = None

    @classmethod
    def from_tree_sitter_raw_symbol(
        cls,
        ts_symbol: RawTreeSitterSymbolData,
        path: Path,
        scope: str | None,
        scope_relation: ScopeRelation | None,
        children: list[Self],
        reference_code: str | None,
        delimiter: str | None,
        is_large_file: bool,
        is_overloaded: bool,
        use_padding: bool,
        code: str,
        reified_symbol: ReifiedSymbol | None = None,  # TODO this is a hack. fix
    ) -> Self:
        # Copied logic from ctags symbol construction below
        file_code = None

        if use_padding:
            start_line = max(0, ts_symbol.start_line - BLIND_PADDING_TOP)
            end_line = ts_symbol.end_line + BLIND_PADDING_BOTTOM
        else:
            start_line = ts_symbol.start_line
            end_line = ts_symbol.end_line
        s_code = "\n".join(code.split("\n")[start_line - 1 : end_line + 1])
        if is_large_file or is_overloaded:
            from shared.chunking.text_splitter import split_text

            s_code_chunks = split_text(
                text=s_code,
                chunk_size=CHUNK_SIZE,
                chunk_overlap=CHUNK_OVERLAP,
            )
            symbol_code = s_code_chunks[0].text if len(s_code_chunks) > 1 else s_code
        else:
            symbol_code = s_code
            file_code = code

        raw_symbol = cls(
            parser_kind=ParserKind.TREE_SITTER,
            symbol_kind=ts_symbol.symbol_kind,
            name=ts_symbol.name,
            path=path,
            scope=scope,
            scope_relation=scope_relation,
            children=children,
            start_line=ts_symbol.start_line,
            end_line=ts_symbol.end_line,
            symbol_code=symbol_code,
            file_code=file_code,
            reference_code=reference_code,
            delimiter=delimiter,
            is_large_file=is_large_file,
            is_overloaded=is_overloaded,
            reified_symbol=reified_symbol,  # TODO hack
        )
        return raw_symbol


class RawSymbolCollection(BaseModel, abc.ABC):
    data: dict[str, RawSymbolData]

    # @classmethod
    # @abc.abstractmethod
    # def from_static_analysis(cls, code: str, root_rel_path: Path) -> Self | None:
    #     pass

    @classmethod
    @abc.abstractmethod
    def from_llm(cls, code: str, root_rel_path: Path) -> Self | None:
        pass

    @abc.abstractmethod  # todo: unabstract this
    def to_dict(self) -> dict[str, RawSymbolData]:
        pass


def disambiguate_header(code: str, fallback: Lang) -> Lang:
    llm = ChatOpenAI(model="gpt-4o", temperature=0, request_timeout=60)
    system_prompt = textwrap.dedent("""\
        You are a software engineering expert that determines whether a header file corresponds to C or C++ code.

        Header files ('.h' extension) are used in both C and C++. Many C headers are written to be compatible with both languages.
        In particular, the use of `#ifdef __cplusplus` and `extern "C"` does not by itself indicate that the code is C++.
        These constructs are commonly used to allow a C header to be included in a C++ project.

        You will be given source code from a header file and must answer whether the code corresponds to:
        - 0 if the code is valid as C (even if it includes compatibility for C++)
        - 1 if the code is valid only as C++ or uses C++-only features (e.g., templates, classes, namespaces, overloading, references)

        Assume the code will be compiled as-is and determine the minimal language required for the code to compile correctly.
        You will be given the source code in the following format:

        File contents:

        <file_contents>

        You only respond with a single number to indicate your response:
        - 0 if the code corresponds to C
        - 1 if the code corresponds to C++
    """)
    user_prompt = f"File contents:\n\n{code}"

    try:
        c_or_cpp_raw = llm.generate_response(
            system_prompt=system_prompt, user_prompt=user_prompt
        )
        zero_or_one = int(c_or_cpp_raw)
        match zero_or_one:
            case 0:
                return Lang.C
            case 1:
                return Lang.CPP
            case _:
                return fallback
    except OpenAIError as e:
        print(
            f"OpenAI API error encountered: {e}. Using fallback {fallback} for header analysis."
        )
        return fallback
    except ValueError as e:
        print(
            f"Failed to parse integer from LLM response: {e}. Using fallback {fallback} for header analysis ."
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
