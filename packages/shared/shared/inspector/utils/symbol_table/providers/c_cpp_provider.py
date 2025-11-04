from shared.inspector.utils.symbol_table.base import LanguageProvider
from shared.inspector.utils.symbol_table.import_resolvers.c_cpp_resolver import (
    CCppResolver,
)
from shared.inspector.utils.symbol_table.symbol_parsers.c_cpp_parser import CCppParser


class CCppLanguageProvider(LanguageProvider):
    """Language provider for C and C++ (treated as a single language family)."""

    language = "c_cpp"

    @classmethod
    def get_parser(cls) -> CCppParser:
        return CCppParser()

    @classmethod
    def get_resolver(cls) -> CCppResolver:
        return CCppResolver()
