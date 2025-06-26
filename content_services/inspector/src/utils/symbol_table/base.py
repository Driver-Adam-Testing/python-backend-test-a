from abc import ABC, abstractmethod
from pathlib import Path
from typing import ClassVar

from utils.lang_specialization.symbol_common import RawTreeSitterSymbolData
from utils.treesitter_drivers.base import DriverTree


class SymbolParser(ABC):
    """Abstract base for language-specific symbol parsing."""

    # Required class attributes
    language: ClassVar[str]
    fqn_delimiter: ClassVar[str]
    tree: type[DriverTree]

    @abstractmethod
    def parse_file(
        self,
        fpath: Path,
        project_root: Path,
    ) -> tuple[
        list[RawTreeSitterSymbolData],  # symbols
        list[RawTreeSitterSymbolData],  # imports
        dict[RawTreeSitterSymbolData, list[RawTreeSitterSymbolData]],  # containment_map
    ]:
        """Parse a single file and return symbols, imports, and containment."""

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


class ImportResolver(ABC):
    """Abstract base for language-specific import resolution."""

    language: ClassVar[str]

    @abstractmethod
    def resolve_import(
        self,
        current_file: Path,
        import_str: str,
        project_files_to_symbols_map: dict[Path, list[RawTreeSitterSymbolData]],
    ) -> Path | list[Path] | None:
        """Resolve an import string to a project file path."""

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
    def get_resolver(cls) -> ImportResolver:
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
