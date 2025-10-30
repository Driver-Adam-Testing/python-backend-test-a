from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar, Self

import tree_sitter
import tree_sitter_c
import tree_sitter_c_sharp
import tree_sitter_cpp
import tree_sitter_go
import tree_sitter_java
import tree_sitter_python
import tree_sitter_ruby
import tree_sitter_typescript

from utils.lang_specialization.symbol_common import RawTreeSitterSymbolData

LANGUAGES = {
    "c": tree_sitter.Language(tree_sitter_c.language()),
    "cpp": tree_sitter.Language(tree_sitter_cpp.language()),
    "python": tree_sitter.Language(tree_sitter_python.language()),
    "java": tree_sitter.Language(tree_sitter_java.language()),
    "csharp": tree_sitter.Language(tree_sitter_c_sharp.language()),
    "js_ts": tree_sitter.Language(tree_sitter_typescript.language_typescript()),
    "go": tree_sitter.Language(tree_sitter_go.language()),
    "ruby": tree_sitter.Language(tree_sitter_ruby.language()),
}


class DriverTreeError(Exception):
    pass


@dataclass
class DriverTree(ABC):
    """Abstract base class for all TreeSitter language drivers."""

    tree_sitter_lang: tree_sitter.Language
    tree: tree_sitter.Tree
    source_bytes: bytes
    file_path: Path

    # Class attributes that MUST be overridden by subclasses
    language: ClassVar[str]
    extensions: ClassVar[set[str]]

    @classmethod
    def from_code(cls, code_str: str, file_path: Path | str) -> Self:
        if not cls.language:
            raise DriverTreeError(
                f"No language specified for {cls.__name__}. Override the 'language' attribute."
            )
        ts_lang = LANGUAGES[cls.language]

        # TODO: this is a workaround for TSX/JSX files to use a different parser.
        # We want js/ts/jsx/tsx files to be parsed to the same symbol table.
        if cls.language == "js_ts" and file_path.suffix in {".jsx", ".tsx"}:
            ts_lang = tree_sitter.Language(tree_sitter_typescript.language_tsx())
        parser = tree_sitter.Parser(ts_lang)
        source_bytes = bytes(code_str, "utf8")
        tree = parser.parse(source_bytes)
        return cls(
            tree=tree,
            tree_sitter_lang=ts_lang,
            source_bytes=source_bytes,
            file_path=Path(file_path),
        )

    @abstractmethod
    def extract_imports(self) -> list[RawTreeSitterSymbolData]:
        pass

    @abstractmethod
    def extract_callable_definitions(self) -> list[RawTreeSitterSymbolData]:
        """Extract function/method definitions from the source code."""

    @abstractmethod
    def extract_data_structure_definitions(self) -> list[RawTreeSitterSymbolData]:
        """Extract class/struct/enum definitions from the source code."""

    @abstractmethod
    def extract_function_calls(self) -> list[RawTreeSitterSymbolData]:
        """Extract function/method calls from the source code."""

    @abstractmethod
    def extract_variables(self) -> list[RawTreeSitterSymbolData]:
        pass

    @abstractmethod
    def extract_function_declarations(self) -> list[RawTreeSitterSymbolData]:
        pass

    # TODO!!! consider resurrecting decorator for symbol extractors
    def extract_all_symbols(self) -> list[RawTreeSitterSymbolData]:
        """Extract all symbols from the source code."""
        symbols = []
        symbols.extend(self.extract_imports())
        symbols.extend(self.extract_callable_definitions())
        symbols.extend(self.extract_data_structure_definitions())
        symbols.extend(self.extract_function_calls())
        symbols.extend(self.extract_variables())
        symbols.extend(self.extract_function_declarations())
        return symbols

    def get_node_line_range(self, node: tree_sitter.Node) -> tuple[int, int]:
        """Returns the 1-based line range of a Tree-sitter node."""
        start_line = node.start_point.row + 1  # Convert 0-based row to 1-based
        end_line = node.end_point.row + 1

        # Check if the last byte in the node's span is a newline; adjust if needed
        if self.source_bytes[node.end_byte - 1 : node.end_byte] == b"\n":
            end_line -= 1

        return start_line, end_line

    def __init_subclass__(cls, **kwargs) -> None:  # noqa: ANN003
        """Validate that subclasses define required class attributes."""
        super().__init_subclass__(**kwargs)
        if not hasattr(cls, "language") or not cls.language:
            raise TypeError(f"{cls.__name__} must define 'language' class attribute")
        if not hasattr(cls, "extensions") or not cls.extensions:
            raise TypeError(f"{cls.__name__} must define 'extensions' class attribute")
