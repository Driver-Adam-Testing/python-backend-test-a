from utils.symbol_table.base import LanguageProvider
from utils.symbol_table.import_resolvers.c_cpp_resolver import CCppResolver
from utils.symbol_table.symbol_parsers.c_cpp_parser import CCppParser
from utils.treesitter_drivers.c_cpp_driver import CppCDriverTree


class CCppLanguageProvider(LanguageProvider):
    """Language provider for C and C++ (treated as a single language family)."""

    language = "c_cpp"

    @classmethod
    def get_driver_class(cls):
        return CppCDriverTree

    @classmethod
    def get_parser(cls):
        return CCppParser()

    @classmethod
    def get_resolver(cls):
        return CCppResolver()
