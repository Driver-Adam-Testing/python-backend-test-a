from abc import ABC, abstractmethod
from pathlib import Path
from typing import ClassVar

from utils.lang_specialization.symbol_common import (
    RawTreeSitterSymbolData,
    SymbolKind,
)
from utils.treesitter_drivers.base import DriverTree

from .utils import build_containment_map, to_root_relative


class SymbolParser(ABC):
    """Abstract base for language-specific symbol parsing."""

    # Required class attributes
    language: ClassVar[str]
    fqn_delimiter: ClassVar[str]
    tree: type[DriverTree]

    def parse_file(
        self, fpath: Path, project_root: Path
    ) -> tuple[
        list[RawTreeSitterSymbolData],  # symbols
        list[RawTreeSitterSymbolData],  # imports
        dict[RawTreeSitterSymbolData, list[RawTreeSitterSymbolData]],  # containment_map
    ]:
        code_str = fpath.read_text(encoding="utf8")
        root_rel_path = to_root_relative(fpath, project_root)

        driver = self.tree.from_code(code_str=code_str, file_path=root_rel_path)

        all_syms = driver.extract_all_symbols()
        containment_map = build_containment_map(symbols=all_syms)

        imports: list[str] = []

        for sym in all_syms:
            if sym.symbol_kind == SymbolKind.IMPORT and sym.name is not None:
                imports.append(sym)

        return all_syms, imports, containment_map

    def __init_subclass__(cls, **kwargs) -> None:  # noqa: ANN003
        super().__init_subclass__(**kwargs)
        if not hasattr(cls, "language") or not cls.language:
            raise TypeError(f"{cls.__name__} must define 'language' class attribute")
        if not hasattr(cls, "fqn_delimiter") or not cls.fqn_delimiter:
            raise TypeError(
                f"{cls.__name__} must define 'fqn_delimiter' class attribute"
            )
        if not hasattr(cls, "tree") or not cls.tree:
            raise TypeError(f"{cls.__name__} must define 'tree' class attribute")


class SymbolResolver(ABC):
    """Abstract base for language-specific symbol resolution from imports."""

    language: ClassVar[str]

    @abstractmethod
    def resolve_imports_to_symbols(
        self,
        all_file_imports: dict[Path, list[RawTreeSitterSymbolData]],
        all_files_symbols: dict[Path, list[RawTreeSitterSymbolData]],
        num_workers: int | None,
        project_root: Path,
    ) -> dict[Path, set[RawTreeSitterSymbolData]]:
        """
        Given a file's imports, return all symbols visible through those imports.
        Each language implements its own logic:
        """
        # NOTE: consider making this NOT an abstractmethod, and then having abstractmethods for
        # `resolve_global_imports` (for C#) and `resolve_file_imports` which can be parallelizable

    def __init_subclass__(cls, **kwargs) -> None:  # noqa: ANN003
        super().__init_subclass__(**kwargs)
        if not hasattr(cls, "language") or not cls.language:
            raise TypeError(f"{cls.__name__} must define 'language' class attribute")


class LanguageProvider(ABC):
    """Abstract base that ensures complete language implementation."""

    language: ClassVar[str]

    @classmethod
    @abstractmethod
    def get_parser(cls) -> SymbolParser:
        """Return the symbol parser instance."""

    @classmethod
    @abstractmethod
    def get_resolver(cls) -> SymbolResolver:
        """Return the import resolver instance."""

    @classmethod
    def get_extensions(cls) -> set[str]:
        """Get file extensions - derived from driver."""
        return cls.get_driver_class().extensions

    @classmethod
    def get_fqn_delimiter(cls) -> str:
        """Get FQN delimiter - derived from parser."""
        return cls.get_parser().fqn_delimiter

    def __init_subclass__(cls, **kwargs) -> None:  # noqa: ANN003
        super().__init_subclass__(**kwargs)
        if not hasattr(cls, "language") or not cls.language:
            raise TypeError(f"{cls.__name__} must define 'language' class attribute")
