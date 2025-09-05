from utils.symbol_table_v2.base import LanguageProvider
from utils.symbol_table_v2.import_resolvers.c_cpp_resolver import CCppResolver
from utils.symbol_table_v2.symbol_parsers.c_cpp_parser import CCppParser


class CCppLanguageProvider(LanguageProvider):
    """Language provider for C and C++ (treated as a single language family)."""

    language = "c_cpp"

    @classmethod
    def get_parser(cls) -> CCppParser:
        return CCppParser()

    @classmethod
    def get_resolver(cls) -> CCppResolver:
        return CCppResolver()
